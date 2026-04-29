source "https://rubygems.org"
# Hello! This is where you manage which Jekyll version is used to run.
# When you want to use a different version, change it below, save the
# file and run `bundle install`. Run Jekyll with `bundle exec`, like so:
#
#     bundle exec jekyll serve
#
# This will help ensure the proper Jekyll version is running.
# Happy Jekylling!

# gem "github-pages", "~> 225", group: :jekyll_plugins
# gem "github-pages", group: :jekyll_plugins

gem "jekyll", "= 3.10.0"

# This is the default theme for new Jekyll sites. You may change this to anything you like.
gem "minima", "~> 2.5"

# If you want to use GitHub Pages, remove the "gem "jekyll"" above and
# uncomment the line below. To upgrade, run `bundle update github-pages`.
gem "github-pages", "~> 232", group: :jekyll_plugins

# If you have any plugins, put them here!
# group :jekyll_plugins do
  # gem "jekyll-feed", "= 0.17.0"
  # gem "jekyll-feed", "= 0.15.1"
  # gem "jekyll-feed", "~> 0.12"
# end

# Windows and JRuby does not include zoneinfo files, so bundle the tzinfo-data gem
# and associated library.
platforms :mingw, :x64_mingw, :mswin, :jruby do
  gem "tzinfo", "~> 2.0"
  gem "tzinfo-data"
end

# Performance-booster for watching directories on Windows
gem "wdm", "~> 0.1.1", :platforms => [:mingw, :x64_mingw, :mswin]

# Lock `http_parser.rb` gem to `v0.6.x` on JRuby builds since newer versions of the gem
# do not have a Java counterpart.
# gem "http_parser.rb", "~> 0.8.0", :platforms => [:jruby]

gem "webrick", "~> 1.8"

# Security fixes:
gem "nokogiri", ">= 1.16"
#gem "html-pipeline", ">= 3.0.0.pre1"

# Bug fixes
gem "liquid", ">= 4.0.4"

# No longer included in Ruby as of 3.4
gem "csv"

# Target blank automatically opens all links in a new window.
gem 'jekyll-target-blank'
