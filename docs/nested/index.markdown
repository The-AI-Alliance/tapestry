---
layout: default
title: TODO - nested section "index" page
nav_order: 20
has_children: true
---

# TODO - nested section "index" page

TODO replace with your content (or delete folder).

An example of a nested section. This is the "index" page for the nested section. Note that URLs elsewhere, like in `../index.markdown` are written `{{site.baseurl}}/nested/` to refer to this index page. The YAML block at the top of this page has the setting `has_children: true`.

Note the [`child`]({{site.baseurl}}/nested/child/) page. It is linked from other pages in the site using `{{site.baseurl}}/nested/child`.

The _child pages_ list is automatically shown at the bottom.
