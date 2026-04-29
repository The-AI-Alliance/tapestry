![The AI Alliance banner](https://the-ai-alliance.github.io/assets/images/ai-alliance-logo-horiz-pos-blue-cmyk-trans.png)

# How to Use `microsite-template`

This repo is used as a template to create and publish AI Alliance &ldquo;microsites&rdquo;. It is setup as a GitHub _template repo_, which you can use to create a new repo. Even if you aren't creating a microsite, you can use this procedure to create a new AI Alliance repo for other purposes. Just delete the `docs` directory after creating the repo and skip the steps that don't apply to you.

See also [`GITHUB_PAGES.md`](https://github.com/The-AI-Alliance/microsite-template/blob/main/GITHUB_PAGES.md), which has more advanced instructions for developers.

## Creating Your Repo

These are the main steps, with details below:

> [!TIP]
> If you choose not to do some of the steps now, for example publishing the GitHub pages website immediately (see step 8), create an Issue in the repo for each step to be done later, as a reminder.

1. Create your repo from the [this template repo](https://github.com/The-AI-Alliance/microsite-template).
1. (Optional) Create a _project_ (i.e., a dashboard) to track your work. Click the _Project_ tab in the repo GitHub page and then either click the _+ New project+_ button or if you want your project to join an existing dashboard, click the _Link a project_ button and find the correct project. By default, project #39, _Misc. Alliance Tasks_, will be used in the next step.
1. Convert placeholder template _variables_ in many files to the correct values, using the [`finish-microsite.sh`](https://github.com/The-AI-Alliance/microsite-template/blob/main/finish-microsite.sh) script. Run `finish-microsite.sh --help` for details or see the expanded description below.
1. Push your local changes upstream.
1. Modify the "header buttons" in `docs/_includes/header_buttons_custom.html` to be what you want to appear at the top of each page. See the [OTDI](https://the-ai-alliance.github.io/open-trusted-data-initiative/) site for an example customization. Or if you don't want any buttons, delete the contents of that file (but don't delete the file...).
1. Add your initial custom content for the pages in the `docs` directory. Delete the files you don't use, e.g., `second_page.markdown` and the `nested` folder. (They are there to provide examples.)
1. Add your initial custom content to the `README.md`.
1. **If** you plan to publish the website from the `latest` branch, merge changes to that branch from `main`.
1. Edit the repo's _Settings_. 
    1. On the repo's home page in GitHub, click the _Settings_ "gear" on the upper right-hand side. 
    1. Click the checkbox labeled _Require contributors to sign off on web-based commits Loading._ (Near the top under _Repository name_.) 
    1. Scroll down to _Features_ and click _Discussions_ to enable them (unless you don't want them; in this case, remove the URL on the `docs/contributing.markdown` page!).
        1. Click the green _Setup discussions_ button, then edit and submit the "welcome" message. (The default is usually fine.)
    1. On the left-hand side, click the link for _Pages_. Under _Branch_, select the `main` or `latest` branch depending on which one you want to use, then select the `/docs` directory. (**NOTE:** Make the repo is _public_ or else the pages won't get published.)
1. Add the website in the appropriate location on the Alliance GitHub organization [README](https://github.com/The-AI-Alliance/) and the Alliance GitHub [website](https://the-ai-alliance.github.io/#the-ai-alliance-projects). 
1. Delete the files `README-instructions.md`, `finish-microsite.sh`, and any of the `LICENSE.*` files that don't apply to your project.
1. Final steps.

> [!NOTE] 
> We are planning to automate as many of the manual steps as we can.

Let's look at these steps in more detail.

### 1. Create your repo from the `microsite-template`.

1. Go to the [`microsite-template`](https://github.com/The-AI-Alliance/microsite-template) repo. 
1. Click the right hand-side green button _Use this template_ and select _Create a new repository_. 
1. Select _The-AI-Alliance_ as the owner account.
1. Enter a unique name for the new repo. I'll use `ai-for-evil-project` as an example here.
1. Enter a description (recommended but optional). 
1. Select _public_ or _private_. You will need the repo to be public to publish a website from it, but you may choose to keep it private initially.
1. click _Create repository_.

See [these GitHub instructions](https://docs.github.com/en/repositories/creating-and-managing-repositories/creating-a-repository-from-a-template) for more details.

### 2. Create or associate a _project_ dashboard to track your work. (Optional)

This step is optional; do it if you want to specify a particular _dashboard_ to manage your issues backlog. While in your GitHub repo, click the _Projects_ tab and either create a new project using the _+New project_ button or associate an existing project with your repo using the _Link a project_ button to browse the [list of current projects](https://github.com/orgs/The-AI-Alliance/projects) and pick one to use. 

If you don't specify a project in the next step of this process, the default will be used, [#39: Misc. Alliance Tasks](https://github.com/orgs/The-AI-Alliance/projects/39).

If you don't want to use a dashboard at all, relying instead on the issues list in the repo, then search the `*.markdown` files and the `.github/**/*/yaml` files for references to a "dashboard" and delete them. 

If you create a new project or decide to use a different one from the default, note the dashboard _number_ in the URL; you'll need it for the next step.

At this time, the project number `N` is used in the following places:
    1. The `projects: [The-AI-Alliance/N]` entries in `.github/ISSUE_TEMPLATE/*.yaml` files.
    1. The line in `docs/contributing.markdown` with `See also the [project board](https://github.com/orgs/The-AI-Alliance/projects/N/)`.

### 3. Convert the placeholder _variables_.

> [!NOTE]
> This step is the only one where you need to work locally on your laptop, vs. working through the GitHub UI. It won't be feasible on Windows machines. If you have any problems doing this step, ask Dean Wampler for help.

Now you have to use the `git` command-line tool, which is built into MacOS, to _clone_ your repo locally and run a script that replaces placeholder _variables_ with the values that are correct for your repo.

Open the `terminal` application. It will show a command prompt at your home directory, e.g., `/Users/deanwampler` for Dean Wampler.

Type in the following command for your repo:

```shell
git clone https://github.com/The-AI-Alliance/REPO_NAME.git
cd REPO_NAME
```

Here `cd` is the _change directory_ command that changes your current working directory to be the root directory of the repo you just cloned.

Now, if you are using this repo for a website, all the website content is under the `docs` directory. However, the script also edits the top-level `README.md`, `Makefile`, and possibly other files.

Your new repo will have placeholder values for the project name, associated focus area, etc. We'll fix those values using the "shell" script [`finish-microsite.sh`](https://github.com/The-AI-Alliance/microsite-template/blob/main/finish-microsite.sh), which replaces the placeholder _variables_ with appropriate strings for your project.

To see the available required and optional arguments, run this command:

```shell
./finish-microsite.sh --help
```

If you run the script without any arguments, it will prompt you for all the values. There are a lot of them, but only the first few values require your input; default values are shown for all the others, which are usually sufficient:

```shell
./finish-microsite.sh 
```

You can also specify the required arguments directly, which is faster if you know what to use. Currently, there is only one required argument, the human-readable title for the website. For example, for a repo named `ai-for-evil-project`, the required command would be the following:

```shell
./finish-microsite.sh --microsite-title "AI for Evil Project" 
```

> [!NOTE]
> The title has to be in quotes if it has nested white space.

Additionally, the following information is important:

> [!NOTE]
> 1. The script will try to use `zsh`. If you don't have `zsh`, but you have `bash` version 5 or later, then use `bash ./finish-microsite.sh ...` to run the script.
> 2. To see the current list of required and optional arguments, run the script with the `--help` flag.
> 3. By default, the website will be published from the `main` branch. If you prefer to use a different branch, we have used `latest` as a convention for many of the microsites. In this case, add the flag `--use-latest`. If you prefer to use a different branch name `BRANCH`, use `--publish-branch BRANCH`.
> 4. The script replaces the content of `README.md` with the content form `README-template.md` (modified with variables replaced), and removes `README-template.md` from the repo. 

> [!WARNING]
> After the script makes changes, it pushes them from the local repo to the upstream repo in GitHub. If you don't want to do that, preferring to push changes upstream later, then add the option `--no-push`. Pushing upstream may fail depending on how your personal GitHub account is configured, etc. Talk to Dean Wampler if you have problems here.

### 4. Edit the website buttons.

> [!NOTE]
> From this point forward, all the subsequent steps can be done on the GitHub UI for your repo.

There are purple "header buttons" that appear on all pages in the website. You can see examples in existing websites, e.g., [OTDI](https://the-ai-alliance.github.io/open-trusted-data-initiative/). The buttons are defined as HTML _anchor_ tags (`<a href="...">...</a>`) in the file `docs/_includes/header_buttons_custom.html`. 

Edit this file to define buttons that work for you. If you don't want any buttons, delete the contents of the file, but _don't delete the file_.

### 5. Add your initial custom content for the pages in the `docs` directory.

There are various `TODO` and example "idioms" in the `docs/**/*.markdown`, `README.md`, and other files that you should replace with your real content as soon as possible, e.g.,

1. Find and replace all occurrences of `TODO` with appropriate content.
2. Rename or delete the `second_page.markdown`. Copy it to add more top-level pages, but change the `nav_order` field to control the order of the pages shown in the left-hand side navigation view. 
3. Rename or delete the `nested` folder and its contents, which is an example of how to create nested content.

> [!TIP]
> Start with `10`, `20`, etc. for the `nav_order` of top-level pages, giving yourself room to insert new pages in between existing pages. For nested pages, e.g., under `20`, use `210`, `220`, etc.

4. See the `nested` directory content as an example of how to do nesting. Note that the metadata fields at the top also define the `parent` and `has_children` fields.
5. Make any changes you want to make in the `docs/_config.yml` file. (None are mandatory.)

For more tips and guidance on development tasks, see also the links for more information in the `README.md` in your new repo. Add a project-specific description at the beginning of that file.

### 6. Add your initial custom content to the `README.md` in the repo.

The `README.md` contains useful _boilerplate_ for contributors, but the preamble at the beginning should be customized with useful "welcome" information about the project.

### 7. Merge changes to the `latest` (or another) branch. (Optional)

By default, the website is published from the `main` branch, for convenience. However, if you chose to use the `latest` branch or another branch (see step 2. above), you'll need to merge the changes in `main` to that branch. We won't provide instructions here, as this is a standard developer practice. However, ask one of the developers on the team for help if needed.

### 8. Edit the repo's _Settings_. 

To publish the website and setup some other repo features, click the _Settings_ "gear" on the upper right-hand side of the repo's top-level page. 

#### 8a. Click the checkbox labeled _Require contributors to sign off on web-based commits Loading._ 

We require [DCO](https://github.com/The-AI-Alliance/community/blob/main/CONTRIBUTING.md#developer-certificate-of-origin) ("Developer Certificate of Origin") checks for all commits. Setting this checkbox turns this on automatically for users making repo edits in the GitHub Web UI.

#### 8b. Enable discussions.

Scroll down to _Features_ and click _Discussions_ to enable them. Click the _Set up discussions_ button and edit the first discussion topic to taste, then post it.

However, if you don't want to enable discussions, then remove the URL on the `docs/contributing.markdown` page.

#### 8c. Publish your website.

On the left-hand side of the _Settings_, click the link for _Pages_. Under _Branch_, select your publication branch, either `main`, `latest`, or a custom branch you specified above. Then select the `/docs` directory and finally, click _Save_.

Your website should be published after a few minutes to `https://the-ai-alliance.github.io/REPO_NAME/``.

> [!TIP]
> At the top of the repo page, click _Actions_ to see the progress of building your website. This action will be executed every time you make a change to a file in your publication branch (i.e., `main` by default). If for some reason building the website fails, this page can provide useful debugging help.

### 9. Add your website to the Alliance GitHub organization page and the Alliance website.

> [!NOTE]
> This step applies for code repos, not just documentation repos.

Add the website to the Alliance GitHub organization [README](https://github.com/The-AI-Alliance/) and the Alliance GitHub Pages [website](https://the-ai-alliance.github.io/#the-ai-alliance-projects).

When you are ready for broader exposure for your site, there are a few places where we have an index to all the &ldquo;microsites&rdquo; and some code-centric projects without microsites. 

1. First find the best place in the [https://github.com/The-AI-Alliance/](https://github.com/The-AI-Alliance/) (`README.md` [direct link](https://github.com/The-AI-Alliance/.github/blob/main/profile/README.md)) or one of the other related [Markdown files](https://github.com/The-AI-Alliance/.github/blob/main/profile/).
2. Make the same change in the corresponding `*.markdown` page in the GitHub organization microsite: [https://the-ai-alliance.github.io/](https://the-ai-alliance.github.io/) (`index.markdown` [direct link](https://github.com/The-AI-Alliance/the-ai-alliance.github.io/blob/main/docs/index.markdown) or sibling pages.)

> [!NOTE]
> _**You only need to edit the appropriate .github file**_ (step #1), because we can automatically propagate the changes to the second file. 

1. Find the right section in the `README.md` or related page where your project belongs.
1. Find the correct table row in the section where it should be inserted.
1. Copy the _**two**_ rows (`<tr>...</tr>`) either above or below this point and insert them.
1. Edit all the details in the rows accordingly for your project. Note that if you didn't create a project dashboard in the previous step, you will delete that item in one of the table cells (`<td>...</td>`). You may decide to add or remove other links, too.

After editing the [.github page](https://github.com/The-AI-Alliance/.github/blob/main/profile/), notify Dean Wampler ([email](mailto:dwampler@thealliance.ai), [Slack](https://ai-alliance-workspace.slack.com/team/U068AL1C30E)), who will run a tool that will copy the changes to the [https://the-ai-alliance.github.io/](https://the-ai-alliance.github.io/) site. (This process is described in the [the-ai-alliance.github.io](https://github.com/The-AI-Alliance/the-ai-alliance.github.io/) repo.)

### 10. Delete the files `README-instructions.md`, `finish-microsite.sh`, and any of the `LICENSE.*` files that don't apply to your project.

The first two files,`README-instructions.md` (this file!) and `finish-microsite.sh`,  are no longer needed, so you can remove them from your repo. Select each one in the GitHub UI and click the `...` menu on the upper right-hand side, then select _Delete file_.

Similarly, you may not need all three `LICENSE.*` files:

* `LICENSE.Apache-2.0`: Recommended for code.
* `LICENSE.CC-BY-4.0`: Recommended for documentation.
* `LICENSE.CDLA-2.0`: Recommended for datasets.

### 11. Final steps.

If you are using a separate publication branch, e.g., `latest`, don't forget to merge all changes from `main` to the publication branch and push both branches upstream, e.g., `git push --all` (when using the CLI in a terminal).

You should now have a published website and you should know how to edit the content. Reach out to Dean Wampler ([email](mailto:dwampler@thealliance.ai), [Slack](https://ai-alliance-workspace.slack.com/team/U068AL1C30E)), Joe Olson ([email](mailto:jolson@thealliance.ai), [Slack](https://ai-alliance-workspace.slack.com/team/U06LFUAM5HN)), or Adam Pingel ([email](mailto:apingel@thealliance.ai), [Slack](https://ai-alliance-workspace.slack.com/team/U06J2U2921F)) if you need help.
