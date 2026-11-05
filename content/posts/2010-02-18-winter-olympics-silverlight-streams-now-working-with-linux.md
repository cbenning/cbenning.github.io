+++
title = "Winter Olympics Silverlight streams now working with linux!"
date = 2010-02-18
[extra]
categories = ["Linux", "Opensource"]
+++

I finally got the streams on <a href="http://www.ctvolympics.ca/video/">http://ctvolympics.ca</a> working on linux using firefox 3.5.7 and <a href="http://www.go-mono.com/moonlight/prerelease.aspx">moonlight 3 preview 2</a>.

Once the plugin is installed, performance may not be super hot. To remedy this, disable the effects in moonlight by running this command in a terminal:

```sh
> MOONLIGHT_OVERRIDES=effects=no
```

Then restart firefox. For other issues, checkout the moonlight <a href="http://www.mono-project.com/Moonlight/OlympicsPlayerIssues">issues</a> page.
