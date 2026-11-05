+++
title = "Google Hangouts plugin crashes in Debian Testing 64-bit"
date = 2013-11-12
[taxonomies]
tags = ["Linux", "Debian", "Google", "Hangouts"]
+++

After an update the other day, Google Hangouts stopped working in Firefox and in Chrome. The symptoms were a collection of items, 
including the browser not registering that the plugin was installed, a prompt saying the plugin has crashed and a message in dmesg
about the plugin segfaulting. It took me a while to find the correct search term and log entry to end at the solution that solved it 
for me. 

I found the log file in '~/config/google'. After examining I found the following mixed in the messages:


```bash
cat ~/.config/google-googletalkplugin/gtbplugin.log

...
... Connection to GoogleTalkPlugin failed, reason=111
...
```


After some searching, I ended up finding a <a href="http://productforums.google.com/forum/#!topic/hangouts/vYsaeEnXJXs">thread in Google Support</a> with a number of suggestions.

Ultimately, I found that my update on Debian pulled down 'libudev1' when 'libudev0' was already installed. There was no conflict, but the plugin seemed to use 'libudev0' even though it required 'libudev1'. Simply
<b>uninstalling libudev0</b> was enough to do it for me, but if you need to keep it for some reason, one can force the plugin to use 'libudev1' with a rather-hacky symbolic link:


```bash
ln -s /lib/x86_64-linux-gnu/libudev.so.1 /opt/google/chrome/lib/libudev.so.0 
```


I hope this helps someone, as I found it took much longer than I'd like to find this solution, even though it was not that uncommon.






