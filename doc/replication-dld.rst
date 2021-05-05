############################################################
Detailed level design of FDMI-based asynchronous replication
############################################################

Overview
========

Definitions
===========

Scheduler
    An application that receives FDMI records and decides what and how to
    replicate.

Replicator
    An application that executes replication tasks received from Scheduler.

HIFREC
    HIerarchical FDMI REcord Classifier. Extensible API that allows to classify
    FDMI records using some classification criteria.


Requirements
============

Dependencies
============

Design Highlights
=================

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

- scalability

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

- Transient failure handling

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

Logical Specification
=====================

Component overview
------------------

TODO describe scheduler and replicator
TODO describe hierarchical FDMI record classifier HIFREC
TODO describe FDMI record reductor FRERED

Scheduler design
----------------

- deduplicates and persists incoming FDMI records
- has it's own index in DIX
- sends work items to the replicator
- distributes the load over replicators
- each scheduler instance runs at most on one node
- there is a list of nodes where a scheduler instance could run. HA ensures
  that it's always running

Scheduler data structures
.........................

- in a distributed index

  - all FDMI records received

    - key: index fid + key size + key + HA epoch + timestamp
    - value: operation + value (in) + value (out) + pointer in BE log for this
      operation + list of all CASes that are handling this operation + list of
      CASes that haven't pruned this record

- in a distributed index and also in RAM

  - list of distributed persistent state machines that are being executed by
    the scheduler instance
  - list of replicators
  - scheduler configuration


Scheduler subroutines
.....................

- init()/fini()

  - Motr client
  - FDMI service
  - FDMI plugin to receive FDMI records

- FDMI record API
- distributed persistent SM API

  - create()/destroy()
  - open()/close()
  - state()
  - state_set()
  - next_event()
  - list_all()

- Replicator call API


Replicator design
-----------------

- just executes the commands sent from scheduler (example: replicates)
- doesn't have it's own persistent state
- has volatile state which keeps track of what has been executed and what
  hasn't
- returns this state back to scheduler on request

Replicator data structures
..........................

Replicator subroutines
......................

- Replicator call API
- S3 API invocations (including non-standard calls)


HIFREC design
-------------

HIFREC data structures
......................

HIFREC subroutines
..................

State specification
-------------------

Threading and Concurrency Model
-------------------------------

Conformance
===========

Tests
=====

O Analysis
==========

Implementation plan
===================

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

References
==========
