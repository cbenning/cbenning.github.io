+++
title = "Converting those pesky .m4a files to .mp3 on Linux"
date = 2011-08-06
[extra]
categories = ["Linux", "Opensource"]
+++

Here is a nice one-liner to convert a .m4a audio file to a .mp3 file:

```sh
$ faad -o - input_file.m4a | lame - output_file.mp3
```

Note: Make sure you have lame and faad installed. In debian they are just 'faad' and 'lame' packages.
