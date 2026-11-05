+++
title = "ImportError: No module named xen... on fresh compiled Xen 4.0.1 with Debian/Ubuntu"
date = 2011-01-25
[extra]
categories = ["Kernel", "Linux", "Opensource", "Programming", "Research", "Virtualization"]
+++

This took me a few hours to find in the mailing list and I thought I would share it with a title that people would find if googling for a solution.

I compiled a fresh copy of Xen 4.0.1 and all of the tools that come along with it. I immediately rebooted and tried to run "xm" to check the status of the system. Any variation on any xen-related command led to me something along the lines of this:


```sh
ImportError: No module named xen.xm
```


The cause is that xen installs all of the python tools into ﻿﻿<code>/usr/lib/python2.6/site-packages/</code> which is not by default in pythons path on a Debian (or Ubuntu) machine. After several hours of searching I found <a href="http://lists.xensource.com/archives/html/xen-users/2010-05/msg00820.html">this</a> post describing the solution.
<br /><br/>
When installing the compiled tools, pass this option to the makefile:

```sh
make install-tools PYTHON_PREFIX_ARG="--install-layout=deb"
```

Enjoy
