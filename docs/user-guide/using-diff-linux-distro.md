# Using different Linux distributions

!!! example "This page is currently under construction"

    Hey there from NucciTheBoss! cleantest is not yet able to support multiple Linux distributions like Debian,
    CentOS Stream, Alma Linux, Fedora, etc. The only distro officially supported right now is Ubuntu, mostly because
    Ubuntu is my distro of choice, and well... I work at Canonical. You can to pull your own images with the LXD test
    environment provider, but I have not gotten around to making that example yet. 

    Mostly what needs to be done to support multiple distros is to refactor the `LXDDataStore` class. Currently I have
    the defaults hardcoded in, but I would like to potentially make cleantest more intelligent. Rather than hardcode,
    I would like to enable querying of the `images:` endpoint and other endpoints. That information can then be loaded
    in at runtime so that users will always have an update-to-date image list. Please bear with me while I work 
    to make cleantest even better!

    __Multidistro support will be added in cleantest 0.4.0__