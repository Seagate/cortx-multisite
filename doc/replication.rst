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
- no read/write to the same index from different processes at the same time
- change # of replicator dynamically
- describe how to define replication policies and what to support

Design highlights
=================

S3server writes a piece of metadata when a new object is uploaded or some
information about the object is updated. This piece of metadata is collected by
replication logic using FDMI, and it's also used to determine what to replicate
and where to replicate to.

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

Analysis
========

Scalability
-----------

TODO describe Scheduler scalability price
TODO describe Replicator scalability

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

References
==========

#. `FDMI DLD
   <https://github.com/Seagate/cortx-motr/blob/main/fdmi/fdmi.c#L24>`_
#. `CORTX R2 Architecture
   <https://seagatetechnology.sharepoint.com/:p:/r/sites/gteamdrv1/tdrive1224/_layouts/15/Doc.aspx?sourcedoc=%7BFBCC2A18-6D77-4576-BACB-AF5682A8C60F%7D>`_

