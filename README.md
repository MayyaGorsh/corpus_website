# Website - Russian language speech practice corpus

_Only displaying the parts that I did in this project. Get the full repository at [/yudinatatiana/big_project_corpora](https://github.com/yudinatatiana/big_project_corpora/tree/main)
_
This is a part of a project by our team. We created a website with several subcorpuses, each of them working in with a different database and displaying the data gathered by linguists. The code features use of SQL, Jinja2, Bootstrap and Flask.

The parts that I realized are:
### Nominations corpus

This is a vast dictionary of words that people use for labeling others. It features:
- Search in all nominations.
- Home page that displays all nominations as cards.
- Template for rendering an individual page, containing all the information about it, which is requested from a database in real time.

### Court descision corpus

This is an archive of court documents from several different instances of Russian court. It features:
- Hub page with the description, statistics on all corpus and two tables, containing links to all combinations of years and instances.
- Template for rendering a page for a specific year and court instance. This page features a "download all" and "view" and "download" for each document.
- Pagination for displaying large quantities of documents.
- Filter by year used when searching through large quantities of documents.
