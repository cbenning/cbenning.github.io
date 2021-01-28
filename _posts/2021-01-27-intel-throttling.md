---
layout: post
title: Intel CPU Throttling
categories: [intel, linux, cpu]
tags: [Linux,cpu,intel]
status: publish
type: post
published: true
comments: true
meta:
  _edit_last: '1'

---

# Finding a solution to strange CPU throttling on Linux

I have a `Lenovo L590`, a mid-tier thinkpad. Sick of 1 hour battery life on my old laptop, I picked the CPU with the lowest power consumption available for this model at the time, the `Intel i5-8265H`. The CPU has a 1.6GHz base clock and a 3.4GHz boost clock.

I use it happily for light work, like browsing and development side projects etc. But when Covid hit I was finding myself using Zoom (and other non-hardware accelerated conferencing tools) constantly. I started noticing that the calls would get choppier and slower the longer the call lasted.

After some investigation, I realized that my fan was never coming on and the CPU was getting hot and throttling itself progressively further and further down until it could find a place it could avoid overheating at. To my surprise, I was seeing that my CPU firmware (not the governor) was throttling itself down as far as 800 MHz to keep from overheating, and yet always staying under 70 deg Celcius.

The pattern I was seeing was that the CPU would run at a healthy clock-speed and boost up frequently until it hit exactly 70 degrees, at which point the fan would never engage at any RPM (which I was able to validate using thinkfan) and would begin to aggressively clock down all while staying at exactly 70 degrees under load.

# Using `thinkfan` to avoid downclocking

The first assumption was that Lenovo had setup an embarassingly poor fan-curve and the solution was to force my own fan curve. 

I setup [thinkfan](https://github.com/vmatare/thinkfan) and began to tinker. The intention was to force a new fan curve so that the fan would keep the CPU cool enough to avoid clocking down.

For benchmarking I used:
```
sysbench --threads=8 --test=cpu --time=120 run
```

My original sysbench score before any tinkering:
```
events per second:  5432.80
```


I did a lot of experimentation with the fan curve and could never get quite right, things still seemed artificially stuck at 70 degrees and the CPU was never seeming to kick into high gear. 
```
echo "watchdog 0" > /proc/acpi/ibm/fan
echo "level 4" > /proc/acpi/ibm/fan
watch -n 1 cat /proc/acpi/ibm/fan
```

I started to experiment with benchmarking the CPU while having the fan pinned to a high RPM just to see what would happen. I noticed about a 10% improvement in performance from pinning the fan, but It wasn't what I was hoping for.

```
events per second:  6005.07
```

# Using `throttled` to solve the real problem

While I was combing through Lenovo forums I stumbled upon [throttled](https://github.com/erpalma/throttled)

This tool completely unscrewed things for me. Instantly the CPU was spiking up to 3.4GHz under load, passing 70 degrees and the built-in fan curve would kick in and cool it back down. After using this tool, I was able to actually remove thinkfan altogether.

The new sysbench score:
```
events per second:  7457.87
```

After seting up `throttled` and setting my fan curve back to auto I was able to achieve a 28% sustained benchmark performance. And even more impressively the boost clock actually went above 3.4GHz.

Beyond simple benchmark performance however the more aggressive upper clock and the improved ability to sit at the base clock, the machine is significantly snappier while using the interface and just feels much less sluggish.

If you run Linux on a laptop with a CPU in that rough class I suggest experimenting with `throttled`