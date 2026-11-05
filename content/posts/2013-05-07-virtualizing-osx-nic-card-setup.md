+++
title = "Virtualizing OSX: Nic card setup"
date = 2013-05-07
[extra]
categories = ["Virtualization"]
+++

If you are automating anything with virtual machines, you likely will be automatically assigning MAC addresses to Nic cards. If you are using any OSX guests, you may have issues around new Nic cards being assigned and having them come up without human interaction. To force OSX to register and bring up new Nics, run the following:

```sh
networksetup -detectnewhardware
```

Applying that to the virtualization case, you can use <em>Automator</em> to create and <em>Application</em> that runs an <em>AppleScript</em> with the above command, and set it to run on login.

