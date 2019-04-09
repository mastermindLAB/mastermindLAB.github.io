---
title: "Google Analytics Implementation into my website"
date: 2019-04-09
tags: [Data Analysis]
header:
  image: "/images/google_analytics/google_analytics.gif"
  excerpt: "Data Science, Data Visualization, Data analysis"
  overlay_image: /images//google_analytics/google_analytics.gif
  overlay_filter: rgba(0, 19, 26, 0.5)
  caption: "Google analytics"
---

Google Intelligence Analytics helped me learn more about my website viewers with a few simple questions -- like how many people visited my Data science page, my photography page, the real time viewer and which page they spend more time. I have managed to implement google analytics into my github page which was build on top of Jekyll →

It's simple straight forward method to implement google analytics into Jekyll.

Step 1 : Go to your **_layouts** page, you will find **default.html** you have to copy & past the script from Google analytics inside the <head> section.

```html
<html lang="{{ site.locale | slice: 0,2 | default: "en" }}" class="no-js">
  <head>
    <!-- Global site tag (gtag.js) - Google Analytics -->
<script async src="https://www.googletagmanager.com/gtag/js?id=UA-XXXXXXXXX-3"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());

  gtag('config', 'UA-XXXXXXXXX-3');
</script>

  </head>
```
You will find this script at your Admin→property setting→Traking info→Taking Code→Global Site Tag (gtag.js) section.  

Step 2: In your **_config.yml** file just add your Tracking ID some thing like this →

```html
# Google Analytics
google_analytics_key: UA-XXXXXXXXX-3 # input your own code Here.

```

This can be found in google analytics Admin panel under property settings.

Here your go you should see this! Once you have successfully do this simple steps mentioned.

### Happy Google Analytics

<img src="{{ site.url }}{{ site.baseurl }}/images/google_analytics/google_analytics.gif">
