======================
FDMI in Multisite work
======================

The purpose of this document is to provide a list of FDMI features that are
needed for multisite work, along with current status of these features. The
list would be used a reference to design and implement missing features.

Overview
========

`FDMI <https://github.com/Seagate/cortx-motr/blob/main/fdmi/fdmi.c#L48>`_
subsystem in `Motr <https://github.com/Seagate/cortx-motr>`_ is going to be
used to get a list of S3 objects that need to be replicated to other sites.

To get a list of Motr tasks for FDMI subsystem to implement missing features we
started with a simple `FDMI-based PoC
<https://github.com/Seagate/cortx/milestone/1>`_  which does the following:
when S3 PUT operation is done there is an FDMI plugin that captures metadata
about this object and prints it to stdout.
