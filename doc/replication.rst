########################################################
High level design of FDMI-based asynchronous replication
########################################################

This document presents HLD of FDMI-based asynchronous replication.
The main purposes of this document are:

- to be inspected by Motr achitects and peer designers to ascertain that high
  level design is aligned with Mero architecture and other designs, and
  contains no defects;
- to be a source of material for detailed level design (DLD) of the same
  component;
- to serve as design reference document.

The intended audience of this document consists of Motr customers, architects,
designers and developers.

Introduction
============

Multisite feature requires replication of objects between 2 different places.
Asynchronous replication allows to copy objects to other destinations in
parallel with client getting response that the objects are written to the first
destination.

Definitions
===========

Motr
    <definition>

S3server
    Software that provides AWS S3 interface to S3 clients and which uses Motr
    to store bucket info, objects etc.

S3 client
    An application that makes S3 requests to store/retrieve the data.

Admin
    Whoever or whatever is responsible for managing the cluster.

Replication policy
    The rule that defines what is replicated and what is the target.

S3 endpoint
    URL that is provided to the S3 client to make S3 I/O against it.


Requirements
============

TODO copy all requirements from MRD, add "related/unrelated" marker for each
one.
TODO add new multisite-specific requirements.

Multisite-specific
------------------

- scalability
- failure handling

  - it MUST be possible to fully lose persistence of a Motr process without
    losing replications for objects.
  - we MUST NOT scan all objects every time a transient failure happens.

- no read/write to the same index from different processes at the same time
- change # of replicator dynamically
- describe how to define replication policies and what to support

Design highlights
=================

S3server writes a piece of metadata when a new object is uploaded or some
information about the object is updated. This piece of metadata is collected by
replication logic using FDMI, and it's also used to determine what to replicate
and where to replicate to.

Workflow overview for an S3 PUT request
---------------------------------------

- S3 client sends PUT request to S3 server
- S3 server looks at replication policies and decides if the data needs to
  be replicated somewhere
- If so, at the end of data I/O S3 server writes it's own metadata that
  tells that the object hasn't been replicated yet and sets special flag
  for DIX operation, and this flag is sent in every CAS request to write
  this kv pair
- CAS produces FOL record, which is grabbed by FDMI source and is sent to
  FDMI filters
- A special FDMI filter checks if this is a record with the flag set by S3
  server and if so, the record is set to an FDMI plugin
- FDMI plugin runs inside the scheduler, so FDMI record is delivered to the
  scheduler
- Scheduler takes the record, deduplicates (because every CAS would have
  the same data), persists the record in a distributed index and then
  replies to FDMI source that the record is no longer needed
- Scheduler has a list of items to replicate in it's distributed index. It
  sends the items to replicators. When the item is replicated S3-level
  metadata is updated to reflect this when needed
- Replicators just do whatever scheduler tells them to do. They don't have
  persistent state.


Implementation
--------------

- having access to the scheduler's own distributed index from only a single
  scheduler and a single Motr process at a time allows to avoid
  synchronisation when accessing the index from different places at the
  same time
- it's better to have schedulers close to the source, to avoid log pruning
  delays because of waiting for acknowledgement from schedulers about
  persisting the FDMI records
- there is an option to add Motr-level replication: in this case ioservice
  or CAS would (explicitly or implicitly) generate an FDMI record that
  would be sent to a scheduler to do replication job
- # of schedulers change is a relatively rare operation, so replicator
  crash wouldn't require distributed algorithms to handle it (like
  redirecting the load to another replicator), because there is only a
  single place on the cluster at any given moment of time where such
  decision is made
- there is a list of servers where each scheduler instance is running, and
  Hare ensures that each scheduler instance is running on at most one of
  such server and it's restarted (on another server if needed) if for some
  reason it stops working


Functional specification
========================

S3 client writes data to an S3 endpoint. The data is replicated according to
replication policies and it is made available eventually at all places it's
supposed to be replicated to.

Logical specification
=====================

Actors: S3 client, S3server, Motr server, Scheduler, Replicator (worker).

TODO add sequence diagrams.

- S3 server:

  - option 1

    - Defines S3-level replication policies
    - Sends "replicate it here and there" data to Motr

  - option 2

    - S3 server just do the I/O as usual

- ioservice

  - FDMI filters only relevant records
  - FDMI records are sent to the right scheduler
  - for each S3 object: FDMI records about it are sent to the same scheduler

- scheduler

  - deduplicates and persists incoming FDMI records
  - has it's own index in DIX
  - sends work items to the replicator
  - distributes the load over replicators
  - each scheduler instance runs at most on one node
  - there is a list of nodes where a scheduler instance could run. HA
    ensures that it's always running

- replicator

  - just executes the commands sent from scheduler (example: replicates)
  - doesn't have it's own persistent state

- general

  - it might be many schedulers
  - it might be many replicators

Conformance
-----------

TODO add detail about each related requirement.

Dependencies
------------

TODO add DTM, FDMI. List required features.
TODO add requirements from HA for scheduler and replicator.

Security model
--------------

TODO analyse security requirements, explain each one. Reference top-level
implementations.

Refinement
----------

TODO add requirements for DLD.

State
=====

TODO Persistent state (also failure handling logic):

- Scheduler distributed index for incoming FDMI records (queue + dedup)
- Scheduler distributed index for SMs
- FDMI on source side: release only on successful persistence response from
  Scheduler
- Replicator: volatile state only, describe properties

TODO decide if SMs for each replication use case need to be there

States, events, transitions
---------------------------

State invariants
----------------

Concurrency control
-------------------

Use cases
=========

TODO describe what kind of metadata is captured for each kind of S3 request

Scenarios
---------

TODO describe what happens for each kind of S3 request

Failures
--------

TODO describe failure handling for each kind of S3 request and for each
possible combination of S3 requests. Take Motr DIX eventual consistency into
account.

Transient failure handling
..........................

- If S3 client fails before PUT operation is complete the PUT operation is
  interrupted and there is nothing to replicate
- If S3 server fails before the last DIX record is persisted - same as S3
  client
- If CAS fails before scheduler replies with "the FDMI record is no longer
  needed" the log would be replayed and the FDMI record would be resent.
  It's not a problem because scheduler does deduplication.
- If scheduler fails it:

  - doesn't lose any FDMI record from CASes, because all such records would
    hold tx reference until the scheduler replies that FDMI record is no
    longer needed
  - has all replication operations (pending to be sent to the replicators
    and that are being processed by the replicator) persisted, so after
    restart it could ask replicators about their state and deal with each
    in-progress replication
  - restarts on another server and continues to accept FDMI records, which
    are now sent to it

- If replicator fails, it just restarts and waits for the new operations
  scheduler sends them to do.


Analysis
========

Scalability
-----------

TODO describe Scheduler scalability price

TODO describe Replicator scalability

- each pool could have an arbitrary number of schedulers attached to it. If
  there are different operations about the same object (or even the same
  operations) they are sent to the same scheduler. Same for kv pair.
- if there is a need to change # of schedulers it could be done in the
  following way:

  - new set of schedulers is added to the Motr configuration
  - old schedulers are stopped (so there are no FDMI records sent to them)
  - scheduler configuration in an index is changed to point to the new set
    of schedulers
  - new schedulers are started, they start receiving FDMI records
  - old schedulers send their records to the new schedulers
  - when there is no work for the old schedulers they are removed from Motr
    configuration

- replicators could be added, removed, they could crash&restart without
  affecting Motr client I/O - FDMI records are sent to the schedulers
  anyway. For each replication item there is a single scheduler that
  manages it
- there is no time or space limit on queue size for replication other than
  space for an index for each scheduler to store replication state to
- there is no requirement for replicators where to be (source side,
  destination side)
- FDMI records are not kept too long on the CAS side. There is no
  requirement for non-blocking availability for the scheduler, so it's fine
  for FDMI source to wait until Motr HA restarts the scheduler somewhere
  else in case of failure


Other
-----

Rationale
---------

TODO describe other approaches and why this one is the best

- recovery after Scheduler transient failure

  - (chosen) Scheduler has distributed persistent state machines
  - Replicator decides what replication task to take and how to handle it

Deployment
==========

Compatibility
-------------

Network
.......

TODO describe how different versions are supposed to work on the same cluster
during upgrade

Persistent storage
..................

TODO describe upgrade process for persistent storage in case if this is ever
needed.

Core
....

Configuration
-------------

- site-level replication: list of sites with the replicas, each site could be
  read-only or read/write, replication direction (if something is written to
  A it doesn't need to be replicated, if something is written to B it has to
  be replicated. Could be done with plugin)
- bucket-level replication: list of buckets, for each: read-only or
  read/write, replication direction
- object-level replication: list of sites, for each site: present/absent
- options

  - read: proxy from another replica or redirect
  - write: # of replicated copies before returning success. Maybe replication
    priority for the copies, where to write before returning success etc. Use
    case: sync replication.

- replication status

  - total size to be replicated, # of metadata entries to replicate for each:
    pool, site, from each site to each site, from each pool to each pool, for
    each bucket
  - map of: schedulers, replicators, pool/scheduler relations
  - flow stats: data, commands
  - queue size for each site/scheduler/bucket, between sites/buckets

- replication control

  - adjust # of: replicators, schedulers
  - bucket-level, site-level, pool-level replication params. Also throttling
    etc.
  - start/stop/queisce/resume

- scanner for existing buckets
- plugins

  - to filter objects for replications
  - to receive events for each stage of replication
  - to decide from where and how (redirect/proxy) to serve S3 GET
  - to decide how many copies to write before returning SUCCESS for S3 PUT

- debugging

  - look for replication stream of events
  - get all logs


Installation
------------

TODO describe how it's installed: new rpms, which component etc.

Upgrade
-------

TODO describe upgrade procedures (persistent state, network)

Implementation plan
===================

List of tasks
-------------

- create a list of all operations that have to be replicated (it's not only
  S3 PUT operation)
- design & implement a way for S3 server to pass "it has to be replicated"
  flag with DIX requests
- move FDMI configuration from conf to DIX
- design & implement scheduler

  - FDMI plugin to receive FDMI records from CASes
  - code to store the records in a distributed index
  - persistent state machines to do the replication for every use case
  - query assigned replicators on restart
  - code to read scheduler configuration from an index
  - code & API to write scheduler configuration to an index
  - code & API to change # of schedulers per pool as described above
  - policies for sending the tasks to replicators (throttling, priorities
    etc.)
  - Motr HA code to restart (possibly somewhere else) in case of failure
  - code & API to get replication progress (query each replicator and
    aggregate) and relevant code in the scheduler to give this info
  - code & API to control replication (start/stop/pause/resume)

- design & implement replicator

  - code to do replication operation for each use case
  - code to reply with it's current state on query from scheduler


Unsorted
========

- Things to consider

  - Where to store replication status.
  - S3 level object metadata has to be replicated as well
  - Replication could be used for rebalancing for capacity feature

- FDMI features that are needed

  - FDMI records persistence. FDMI app has to survive transient failures.
  - "At most once" delivery. Resend in case of failures.
  - Something to deal with permanent failures of FDMI source or FDMI plugin.
  - We can have replication from one Motr cluster to another Motr cluster if
    we allow FDMI app to contain 2 Motr processes that belong to different
    Motr clusters.

 - Single Motr cluster replication

   - Object level, trivial, async: Get list of objects in one Motr pool and
     objects in another Motr pool. Replicate missing. Repeat with configurable
     interval. Do the same for metadata.
   - Motr client level: each Motr client I/O spawns I/Os for more than 1
     object.
   - Object level, async: there are FDMI applications that are watching for
     "Object had been written" FDMI record. Motr client produces this record
     and returns that I/O is successful only when FDMI apps confirm that they
     have persisted the record. Then FDMI application moves the data.
   - DTM way, new dtx, both sync and async: Motr client creates a dtx to
     replicate the object before returning "SUCCESS" for object I/O. Push/pull
     options. Servers involved will initiate the I/O to complete dtx. DTM0 is
     enough for this.

     - failure cases, how to handle them (transient and permanent)
     - DTM0 for transient, integrate with SNS for permanent

   - DTM way, same dtx, sync replication: all object I/O requests (including
     replication) are parts of the same dtx.
   - cob level: each cob I/O spawns

     - Push: FDMI app on the same server as ioservice initiates cob I/O to
       replicate the object whenever ioservice on that server it has incoming
       cob I/O. Allows to read the data from source ioservice only once, FDMI
       apps caches the data until it's transferred to all the targets.
     - Pull: FDMI records are consumed by FDMI apps on the target servers.
       They tell target ioservices to pull the data from source ioservices.
     - Dedicated replicators: FDMI app may live outside of storage nodes. It
       would consume FDMI records about objects and read/write the data as
       usual clients or it could send fops that would move data from one
       server to another.
     - limitations: same striping on both pools.

   Notes

   - FDMI app could either push/pull the data on it's own or tell ioservices
     to do the data movement.

References
==========

#. `FDMI DLD
   <https://github.com/Seagate/cortx-motr/blob/main/fdmi/fdmi.c#L24>`_
#. `CORTX R2 Architecture
   <https://seagatetechnology.sharepoint.com/:p:/r/sites/gteamdrv1/tdrive1224/_layouts/15/Doc.aspx?sourcedoc=%7BFBCC2A18-6D77-4576-BACB-AF5682A8C60F%7D>`_

