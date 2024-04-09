import configparser
import json  # noqa: F401
import os
from pathlib import Path
import pprint  # noqa: F401

import requests
from bs4 import BeautifulSoup
from github import Auth, Github

api_url = "https://api.github.com"
github_url = "https://github.com"
gh = None


def scrape_topic(topic, github_url="https://github.com"):
    """Get the information about projects in a topic.

    Parameters
    ----------
    topic : str
        The name of the topic (and last part of the url)
    github_url : str = "https://github.com"
        The base URL for GitHub.

    Returns
    -------
    ?
    """
    topic_url = github_url + "/topics/" + topic

    result = {
        "repos": {},
        "topics": {},
    }
    topic_data = result["topics"]
    repo_data = result["repos"]

    page = 1
    n_articles = 0
    while True:
        r = requests.get(topic_url, params={"page": str(page)})
        html = r.text

        soup = BeautifulSoup(html, "html.parser")
        body = soup.body

        articles = body.find_all("article")
        n_articles += len(articles)

        # Lets look at the article
        for article in articles:
            divs = article.find_all("div", recursive=False)

            # Reference to GitHub project
            tmp = []
            for tag in divs[0].find_all("a", class_="Link"):
                tmp.append(tag.string)
                tmp.append(tag["href"])
            organization = tmp[0].strip()
            organization_url = tmp[1].strip()
            repo = tmp[2].strip()
            repo_url = tmp[3].strip()

            if organization_url[1:] != organization:
                raise RuntimeError(
                    f"URL for organization '{organization}' different: "
                    f"'{organization_url}'"
                )
            if repo_url != organization_url + "/" + repo:
                raise RuntimeError(f"URL for repo '{repo}' different: '{repo_url}'")

            if repo_url not in repo_data:
                data = repo_data[repo_url] = {}
            else:
                data = repo_data[repo_url]

            data["organization"] = organization
            data["organization_url"] = organization_url
            data["repo"] = repo
            data["repo url"] = repo_url

            # Stars
            for tag in divs[0].find_all("span", class_="js-social-count"):
                stars = str(tag.string).strip()
                data["stars"] = int(stars)

            # Description of the project
            for tag in divs[1].find_all("p"):
                data["description"] = str(tag.string).strip()

            # Topics
            data["topics"] = []
            for tag in divs[1].find_all("a", class_="topic-tag"):
                topic = str(tag.string).strip()
                url = tag["href"]
                data["topics"].append(topic)
                if topic not in topic_data:
                    topic_data[topic] = url

            # Updated time and language
            for tag in divs[1].find_all("relative-time"):
                update_time = tag["datetime"]
                # updated = str(tag.string).strip()
                data["updated"] = update_time
            for tag in divs[1].find_all("span", itemprop="programmingLanguage"):
                language = str(tag.string).strip()
                data["programming language"] = language

        # Check if there is a next page
        if "Load more" in html:
            page += 1
        else:
            break

    return result


def use_api(topic):
    global gh

    if gh is None:
        path = Path("~/.thriverc").expanduser()
        if "GH_TOKEN" in os.environ:
            token = os.environ["GH_TOKEN"]
        elif path.exists():
            config = configparser.ConfigParser()
            config.read(path)
            token = config.get("GitHub", "token")
        else:
            raise RuntimeError(
                "A GitHUb token needs to be supplied in the environment variable "
                "'GH_TOKEN' or in the file '~/.thriverc'."
            )
        auth = Auth.Token(token)
        gh = Github(auth=auth)

    count = 0
    result = {}
    repos = gh.search_repositories(query=f"topic:{topic}")

    for item in repos:
        try:
            fullname = item.full_name
            organization, repo = fullname.split("/")

            result[fullname] = {}
            data = result[organization + "/" + repo]

            count += 1
            data["row"] = count
            data["organization"] = organization
            data["repo"] = repo
            data["url"] = item.html_url
            data["description"] = item.description
            data["created"] = item.created_at
            data["size"] = item.size
            data["id"] = item.id
            if item.license is None:
                data["license"] = ""
            else:
                data["license"] = item.license.name
            data["programming language"] = item.language
            data["updated"] = item.updated_at
            data["stars"] = item.stargazers_count
            data["watchers"] = item.watchers_count
            data["open issues"] = item.open_issues_count
            data["pushed at"] = item.pushed_at
            data["topics"] = item.topics
        except Exception as e:
            print(e)
            print("")
            tmp = vars(item)
            pprint.pprint(tmp)
            print("")
            raise
    return result
