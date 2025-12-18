# Markdown Import/Export
* New nav item called "MD Import/Export"

## Export Functionality (first tab)
* Lists Corpus (should have both Advanced converted files and Simple Converted items) like `/corpus` page
* Clicking an item copies over the markdown document into a subfolder called `exports` udner the output folder from the config
* Add the following to metadata (expected for import) that are similar as Simple Conversion: 
    * Title
    * Author
    * Publication year 
* Example of metadata:
```
---
title: [title_of_work]
author: [author_of_work]
year: [year_of_pub_of_work]
---
```

## Import Functionality (second tab)
* Lists all the markdown files in the input folder (from config)
* When user selects a markdown file, and starts import for it (button):
    * Use the metadata for title/author/pub year
    * If metadata not present, ask user to fill in
* After it starts process of importing up to vectorization (vector embedding):
    * Have a modal asking user if the markdown is sanitized
    * If sanitized can skip right to chunking headings and then content
    * If not santizied perform the sanitization steps that occur in simple conversion

Research the standards as they are setup in simple vectorization for showing pdf files (but show markdown files) and the steps taken. 