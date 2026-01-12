
<div align="center">

![VulcanLab Logo](/assets/logo-sm.png)

# VulcanLab

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)

**A Retrieval-Augmented Generation system.**
</div>

## Documentation

Documentation can be found on these GitHub pages that will explain how to run with docker (easiest) and locally. The notes in thid README are focused more on active development. 

[Official Documentation](https://dominikgorecki.github.io/vulcanlab/)

## General Notes

### Simple vs. Advanced Conversion 

Currently VulcanLab has "Simple Conversion" and "Advanced Conversion" that needs to be turned on via the `Settings → Conversion` page. 

Advanced conversion still uses the output folder to store certain files during the conversion process and the final sanitized markdown document from which chunks are built. This is the **old** approach. 

Simple conversion (recommended) gives you less control, but it's streamlined and works in 90% of cases. All the data is stored in the DB (except the original input pdf) and there is no dependence on the "output" folder. 

**Recommendation** -- Unless you know what you're doing and have a good reason for doing so, do not use the "Advanced Conversion" mode.

### Raw and Sanitized Markdown Documents 
 > ... only stored for reference and inspect after ingesting into chunks...

 After chunks are created, the converted markdown files (raw and sanitized) and all the other in-process files (for advanced) are only stored for reference and inspection. For example, if you click on a parsed in work from the `Corpus` page, you can see the sanitized markdown document so that if you delete it from the output folder (or the DB) this page will show an error (the `corpus/[id]` page) but RAG will still work fine. 


### Repo Active Documentation
[docs/](/docs/) Folder

## Features
*   **[Collection Deep Research](/documentation/features/collection-deep-research.md)**: Curate items and perform academic-quality research with automated refinement and result reuse.
