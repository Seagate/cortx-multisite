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

.. list-table::
    :header-rows: 1

    * - ID
      - Description
      - Is this implemented, and if so, how?
    * - TBD
      - It MUST be possible to get DIX PUT kv pairs in a Motr process which
        doesn't have CAS service that received CAS PUT request for the DIX PUT
        request.
      - It is. FDMI record contains CAS kv pairs, and there is an
        implementation for FDMI record sending/receiving.
    * - TBD
      - It MUST be possible to get CAS kv pair even if CAS was not running at
        the time DIX PUT execution was initiated.
      - It's not. DTM0 is required for this. Some integration work may or may
        not be required.
    * - TBD
      - It MUST be possible to get CAS kv pair even if a Motr process with the
        CAS inside crashes during DIX PUT execution: after CAS PUT is executed,
        but before FDMI record receival is acknowledged by FDMI plugin on FDMI
        source.
      - It's not. It requires sending FDMI records sometime around or after BE
        recovery.
    * - TBD
      - It MUST be possible to determine when FDMI records are never going to
        be resent from FDMI source.
      - It's not. It's needed to provide a way for FDMI plugin to prune records
        that are never going to be received.

        We need to do the following:

        - send FDMI record BE log position (approximate is enough) with each
          FDMI record;
        - send BE log position of discarded records that are never going to be
          replayed again during BE recovery.

        Each CAS would provide such position, and it would be possible to do
        per- storage device pruning.
