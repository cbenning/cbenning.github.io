+++
title = "How to Force Snow Leopard+ to consider a shell script safe."
date = 2013-06-12
+++

You can tell OSX Snow Leopard to consider shell scripts safe to execute without a user prompt. This is useful for automation of certain tasks. You can use any UTI mime-type to allow any filetype you wish. To do so, place the below text in <code>~/Library/Preferences/com.apple.DownloadAssessment.plist</code>


```html
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
	<key>LSRiskCategorySafe</key>
	<dict>
		<key>LSRiskCategoryContentTypes</key>
		<array>
			<string>public.shell-script</string>
		</array>
	</dict>
</dict>
</plist>
```

