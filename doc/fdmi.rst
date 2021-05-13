======================
FDMI in Multisite work
======================

The purpose of this document is to provide a list of FDMI features that are
needed for multisite work, along with current status of these features. The
list would be used a reference to design and implement missing features.


Introduction
============

`FDMI <https://github.com/Seagate/cortx-motr/blob/main/fdmi/fdmi.c#L48>`_
subsystem in `Motr <https://github.com/Seagate/cortx-motr>`_ is going to be
used to get a list of S3 objects that need to be replicated to other sites.

To get a list of Motr tasks for FDMI subsystem to implement missing features we
started with a simple `FDMI-based PoC
<https://github.com/Seagate/cortx/milestone/1>`_  which does the following:
when S3 PUT operation is done there is an FDMI plugin that captures metadata
about this object and prints it to stdout.


Definitions
===========

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD",
"SHOULD NOT", "RECOMMENDED",  "MAY", and "OPTIONAL" in this document are to be
interpreted as described in `RFC 2119 <https://tools.ietf.org/html/rfc2119>`_.


Requirements
============

TODO assign stable IDs

TBD == to be defined

Ballpark estimates:

- are in assumption that I could run a cluster (VM or hardware) and I could
  build & install a new version of Motr with a single command in 10 minutes. If
  this is not the case then the estimates could be doubled, tripled etc.;
- I get support for the issues with existing code (especially outside of Motr)
  in timely manner. If it's not the case then the consequences are the same as
  for the previous item;
- are without code reviews;
- are without landings to ``main`` and/or ``stable`` and/or some similar
  branch;
- are for me;
- depend on my level of motivation. Current estimates are for high level.

.. list-table::
    :widths: 5 30 30 5 25 5
    :header-rows: 1

    * - ID
      - Description
      - Comment
      - Done?
      - How and what else is needed?
      - A ballpark estimate
    * - TBD
      - FDMI source MUST NOT send FDMI record to FDMI plugins before FDMI
        record becomes persistent on the source side
      - It's required to be able to handle crash/restart of CAS correctly. If
        FDMI record is sent before it becomes persistent then it might be a
        case when it's not persisted and FDMI plugin will get a KV pair that
        hasn't been inserted into the catalogue.
      - N
      - Currently a generic fom phase posts FDMI record before BE transaction
        is logged. The solution to this is to defer posting up until BE
        transaction is logged.
      - 1w.
        2h if everything is smooth, a few days if not. Unlikely to take more,
        depends on the stability of existing code.
    * - TBD
      - It MUST be possible to get DIX PUT kv pairs in a Motr process which
        doesn't have CAS service that received CAS PUT request for the DIX PUT
        request.
      - It's needed to be able to get kv pairs from all CASes in a single Motr
        process.
      - N
      - FDMI record is supposed to contains CAS kv pairs, and there is an
        implementation for FDMI record sending/receiving. There is a bug in
        implementation though: kv pairs are being freed too early in CAS, and
        they are not beint sent nor logged to BE log as FOL records. Fix for
        this issue: `cortx-motr/pull/588
        <https://github.com/Seagate/cortx-motr/pull/588>`_.
      - 0d
    * - TBD
      - It MUST be possible to get CAS kv pairs even after FDMI plugin restart.
      - It's needed to handle Scheduler restarts.
      - N
      - Hare MUST notify Motr about Scheduler restart. RPC connections need to
        be re-established after Scheduler restart.
      - 3w-6w. Hare work has to be done by Hare team. Motr RPC work is in FDMI
        and in RPC: a week to several weeks.
    * - TBD
      - It MUST be possible to get CAS kv pair even if CAS was not running at
        the time DIX PUT execution was initiated.
      - This is needed to handle transient process failures (crash/restart
        etc.) from DTX PUT point of view.
      - N
      - DTM0 is required for this. Some integration work may or may not be
        required. It will not be known before DTM0 is landed.
      - Not clear without seeing DTM0 changes. Likely to be done automatically
        or with a very few changes.
    * - TBD
      - It MUST be possible to get CAS kv pair even if a Motr process with the
        CAS inside crashes during DIX PUT execution: after CAS PUT is executed,
        but before FDMI record receival is acknowledged by FDMI plugin on FDMI
        source.
      - This is needed to handle transient process failures (crash/restart)
        from CAS PUT point of view.
      - N
      - It requires sending FDMI records sometime around or after BE
        recovery.
      - 2w - 3months+.
        No code for doing even something close to this is present in Motr right
        now. If we can get away with simply pushing FOL records to FDMI during
        BE recovery then it's a few days (I think it's the case). If no then it
        might be weeks.
    * - TBD
      - It MUST be possible to determine when FDMI records are never going to
        be resent from FDMI source.
      - It's needed to provide a way for FDMI plugin to prune records
        that are never going to be received.
      - N
      - We need to do the following:

        - send FDMI record BE log position (approximate is enough) with each
          FDMI record;
        - send BE log position of discarded records that are never going to be
          replayed again during BE recovery.

        Each CAS would provide such position, and it would be possible to do
        per- storage device pruning.
      - 2d - 2w
    * - TBD
      - It MUST be possible to adjust FDMI filters in runtime.
      - This is needed to adjust replication configuration (what to replicate,
        where to replicate to etc.) in runtime.
      - N
      - We need to do the following:

        - store FDMI filters configuration in a distributed index
        - read FDMI filter configuration from a distributed index during FDMI
          startup
        - add a way to update filter configuration in runtime
        - add a tool to adjust filter configuration in runtime

        Currently we have filters in Motr configuration. Each filter supports
        only one endpoint where to send FDMI records to (this may not enough
        for multisite). Currently there is no code in Motr/Hare to add filters
        to the configuration or to change the filter configuration.
      - Depends on compexity of FDMI filters. If they are like they are now,
        then it's weeks, month or even more. We have no code to read Motr DIX
        from server, it may take a lot of time. Adjusting filter configuration
        in runtime also requires RM locks, which, in turn, requires code to
        work when principal RM changes. It must also be some kind of
        synchronisation between RM locks and DTM operations (to handle crash of
        the code that writes FDMI filter configuration). My estimate is from a
        few weeks to months.
    * - TBD
      - It MUST be possible to adjust FDMI filter targets in runtime.
      - This is needed to configure or reconfigure sets of Schedulers after
        initial cluster bootstrap.
      - N
      - We need to do the same as for the previous requirement.
      - 0
    * - TBD
      - It MUST be possible to determine the outcome of a DIX PUT operation if
        multiple DIX PUT operations were executed for the same key in the same
        distributed index.
      - This is needed to handle sequential and, if required, concurrent object
        metadata updates for the same object.
      - N
      - DTM0 design is required to figure out how to do this and DTM0 landing
        is required to implement this.
      - If DTM0 has the features that are needed and exports the functions then
        it may take 1w-4w.


Prototype
=========

As a part of `FDMI prototype work
<https://github.com/Seagate/cortx/milestone/1>`_ the following was done:

- single node Motr/Hare/`m0crate`/FDMI plugin setup was used;
- a hardcoded FDMI filter was added on FDMI source side to check that FDMI
  records could be filtered before they are sent to FDMI plugins;
- full `m0crate` `DIX` -> `CAS` -> FDMI plugin pipeline was configured and
  implemented. FDMI plugin in this setup prints kv pairs that are originated in
  `m0crate`;
- analysis of what is missing in the current FDMI implementation that is needed
  for FDMI-based replication.

Outcome:

- a branch with the source code https://github.com/somnathbghule/cortx-motr/commits/fdmi-plugin-multisite;
- documentation on how to run the prototype https://github.com/somnathbghule/cortx-motr/blob/fdmi-plugin-multisite/doc/m0sched.rst;
- list of requirements for FDMI for Multisite replication along with approach on how to implement each of them https://github.com/Seagate/cortx-multisite/blob/max/doc/fdmi.rst#requirements;
- GitHub milestone to track the work https://github.com/Seagate/cortx/milestone/1;
- a bugfix for Motr: CAS kv pairs were not added to FDMI records: https://github.com/Seagate/cortx-motr/pull/588;

Further directions

- make a setup with S3server as a source of DIX operations to see object
  metadata in the output of the FDMI plugin that was made as part of the
  prototype;
- land the prototype as an FDMI demo to Motr. There is no such demo at the
  moment;
- incorporate knowledge acquired during prototype work into Multisite designs;
- design, plan and implement missing FDMI features that are needed for
  Multisite work.
