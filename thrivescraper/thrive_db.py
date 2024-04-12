# -*- coding: utf-8 -*-

"""A dictionary-like object for holding THRIVE data
"""

import collections.abc
import logging
import sqlite3

from .table import _Table


logger = logging.getLogger(__name__)


class ThriveDB(collections.abc.MutableMapping):
    """The database underlying THRIVE."""

    def __init__(self, logger=logger, **kwargs):
        self.logger = logger
        self._database_uri = None
        self._db = None
        self._cursor = None
        self._items = {}

        if "database" in kwargs:
            self.database_uri = kwargs.pop("database")
        else:
            self.database_uri = "THRIVE.db"

    def __del__(self):
        """Destructor: need to close the database if any."""

        # Delete any cached objects
        del self._items

        # And close the database
        if self._db is not None:
            self.db.commit()
            self.db.close()

    def __enter__(self):
        self.db.commit()

        return self

    def __exit__(self, etype, value, traceback):
        if etype is None:
            self.db.commit()

    def __getitem__(self, key):
        """Allow [] access to the dictionary!

        Because some of the items, such as template contain state,
        we need to ensure that the same object is used everywhere. Hence
        the self._items array to store the instances.

        Parameters
        ----------
        key : str
            The table name or name of a multi-table item like atoms.

        Returns
        -------
        table : Table
        """
        if key not in self._items:
            self._items[key] = _Table(self, key)
        return self._items[key]

    def __setitem__(self, key, value):
        """Allow x[key] access to the data"""
        raise NotImplementedError(f"Table '{key}' cannot be created yet")

    def __delitem__(self, key):
        """Allow deletion of keys"""
        if key in self:
            self.cursor.execute(f"DROP TABLE '{key}'")

    def __iter__(self):
        """Allow iteration over the object"""
        return iter(self.list())

    def __len__(self):
        """The len() command"""
        self.cursor.execute(
            "SELECT COUNT(*)" "  FROM sqlite_master" " WHERE type = 'table'"
        )
        return self.cursor.fetchone()[0]

    def __contains__(self, table):
        """Return a boolean indicating if a key exists."""
        # Normal the tablename is used as an identifier, so is quoted with ".
        # Here we need it as a string literal so strip any quotes from it.
        if "." in table:
            schema, table = table.split(".")
            schema = schema.strip('"')
        else:
            schema = "main"

        table = table.strip('"')
        self.cursor.execute(
            "SELECT COUNT(*)"
            f" FROM {schema}.sqlite_master"
            f" WHERE type = 'table' and name = '{table}'"
        )
        return self.cursor.fetchone()[0] == 1

    @property
    def cursor(self):
        """A database cursor."""
        return self._cursor

    @property
    def db(self):
        """The database connection."""
        return self._db

    @property
    def db_version(self):
        """The version string for the database."""
        self.cursor.execute("SELECT value FROM metadata WHERE key = 'version'")
        return self.cursor.fetchone()[0]

    @property
    def database_uri(self):
        """The name of the file (or URI) for the database."""
        return self._database_uri

    @database_uri.setter
    def database_uri(self, value):
        if value != self._database_uri:
            if self._db is not None:
                self.cursor.close()
                self._db.commit()
                self._db.close()
                self._db = None
                self._cursor = None
        self._database_uri = value
        if self._database_uri is not None:
            if self._database_uri[0:5] == "file:":
                self._db = sqlite3.connect(self._database_uri, uri=True)
            else:
                self._db = sqlite3.connect(self._database_uri)
            self._db.row_factory = sqlite3.Row
            self._db.execute("PRAGMA foreign_keys = ON")
            self._db.execute("PRAGMA synchronous = normal")
            self._db.execute("PRAGMA temp_store = memory")
            self._db.execute("PRAGMA mmap_size = 30000000000")
            if "mode=ro" not in self._database_uri:
                self._db.execute("PRAGMA journal_mode = WAL")
            self._cursor = self._db.cursor()
            self._initialize()

    def attributes(self, tablename: str):
        """The attributes -- columns -- of a given table.

        Parameters
        ----------
        tablename : str
            The name of the table, optionally including the schema followed by
            a dot.

        Returns
        -------
        attributes : Dict[str, Any]
            A dictionary of dictionaries for the attributes and their
            descriptors
        """
        if "." in tablename:
            schema, tablename = tablename.split(".")
            sql = f"PRAGMA {schema}.table_info('{tablename}')"
        else:
            sql = f"PRAGMA table_info('{tablename}')"

        result = {}
        for line in self.db.execute(sql):
            result[line["name"]] = {
                "type": line["type"],
                "notnull": bool(line["notnull"]),
                "default": line["dflt_value"],
                "primary key": bool(line["pk"]),
            }
        return result

    def close(self):
        """Close the database."""
        self.database_uri = None

    def create_table(self, name, cls=_Table, other=None):
        """Create a new table with the given name.

        Parameters
        ----------
        name : str
            The name of the new table.

        cls : Table subclass
            The class of the new table, defaults to Table

        Returns
        -------
        table : class Table
            The new table
        """
        if name in self:
            raise KeyError(f"'{name}' already exists in the system.")

        self._items[name] = cls(self, name, other)
        return self._items[name]

    def list(self):
        """Return a list of all the tables in the system."""
        result = []
        for row in self.db.execute(
            "SELECT name" "  FROM sqlite_master" " WHERE type = 'table'"
        ):
            result.append(row["name"])
        return result

    def _initialize(self):
        """Initialize the SQLite database.

        The order is a bit tricky, since many tables reference other tables,
        and hence need to be created after the ones that they reference.

        Notes
        -----
            There is an issue with conflicts with SQL keywords. For example 'commit' is
            reserved word. We will use the following convention which partly avoids this
            problem.

            * Table names are plural, e.g. ``commits``. This scans nicely in English
              because it is a table containing zero or more commits.

            * Column names are singular. In this case ``commit`` needs to be escaped
              with double quotes (SQL standard) so the python needs to use single
              quotes ``'"commit"'``

            Apologies for unusual plurals in English like ``category`` -->
            ``categories``!
        """

        # If the database is initialized, the metadata table exists.
        if "metadata" in self:
            return

        # In the future we might need to check the version and upgrade
        # older versions, but now at version 1.0 we are all done!
        # metadata, where we store, get the database version

        table = self["metadata"]
        table.add_attribute("key", coltype="str", pk=True)
        table.add_attribute("value", coltype="str")

        table.append(key="version", value="1.0")
        self.db.commit()

        # row keep Category Commercial organization name description
        # Citation	n_citations	n_citations_url
        # created	created	Age	size	id	license	programming_language
        # last_updated	stars	watchers n_open_issues pushed_at topics

        # The organizations table
        table = self["organizations"]
        table.add_attribute("id", coltype="int", pk=True)
        table.add_attribute("name", coltype="str")

        # The categories table
        table = self["categories"]
        table.add_attribute("id", coltype="int", pk=True)
        table.add_attribute("name", coltype="str")

        table.append(name="none")
        table.append(name="atomistic chemical ml")
        table.append(name="atomistic materials ml")
        table.append(name="atomistic materials")
        table.append(name="atomistic molecular")
        table.append(name="chemical ml")
        table.append(name="computational mechanical")
        table.append(name="experimental analysis")
        table.append(name="granular simulation")
        table.append(name="materials ml")
        table.append(name="mesoscale materials ml")
        table.append(name="mesoscale materials")

        # The repos table
        table = self["repos"]
        table.add_attribute("id", coltype="int", pk=True)
        table.add_attribute("active", coltype="int")
        table.add_attribute("full_name", coltype="str", index="unique")
        table.add_attribute("organization", coltype="int", references="organizations")
        table.add_attribute("name", coltype="str")
        table.add_attribute("archived", coltype="int")
        table.add_attribute("category", coltype="int", references="categories")
        table.add_attribute("created_at", coltype="int")
        table.add_attribute("default_branch", coltype="str")
        table.add_attribute("description", coltype="str")
        table.add_attribute("homepage", coltype="str")
        table.add_attribute("language", coltype="str")
        table.add_attribute("license", coltype="str")
        table.add_attribute("node_id", coltype="str")
        table.add_attribute("pushed_at", coltype="int")
        table.add_attribute("updated_at", coltype="int")

        # # The data table
        # table = self["data"]
        # table.add_attribute("id", coltype="int", pk=True)
        # table.add_attribute("time", coltype="int")
        # table.add_attribute("repo", coltype="int", references="repos")
        # table.add_attribute("size", coltype="int")
        # table.add_attribute("stargazers", coltype="int")
        # table.add_attribute("watchers", coltype="int")
        # table.add_attribute("forks", coltype="int")
        # self.db.execute(
        #     "CREATE UNIQUE INDEX 'idx_data_time_repo'" '    ON data ("date", "repo")'
        # )

        # Citations
        table = self["citations"]
        table.add_attribute("id", coltype="int", pk=True)
        table.add_attribute("citation_url", coltype="str", index="unique")
        table.add_attribute("n_citation_url", coltype="str")

        # Contributors
        table = self["contributors"]
        table.add_attribute("id", coltype="int", pk=True)
        table.add_attribute("name", coltype="str", index="unique")

        # Topics
        table = self["topics"]
        table.add_attribute("id", coltype="int", pk=True)
        table.add_attribute("name", coltype="str", index="unique")

        # The repos-topics join table
        table = self["repos_topics"]
        table.add_attribute("repo", coltype="int", references="repos")
        table.add_attribute("topic", coltype="int", references="topics")
        self.db.execute(
            "CREATE INDEX 'idx_repos_topics' " 'ON repos_topics ("repo", "topic")'
        )

        # Commits
        table = self["commits"]
        table.add_attribute("id", coltype="int", pk=True)
        table.add_attribute("sha", coltype="str", index="unique")
        table.add_attribute("author", coltype="int", references="contributors")

        # The repos-commits join table
        table = self["repos_commits"]
        table.add_attribute("repo", coltype="int", references="repos")
        table.add_attribute("commit", coltype="int", references="commits")
        self.db.execute(
            """CREATE INDEX 'idx_repos_commits' ON repos_commits ("repo", "commit")"""
        )

        self.db.commit()

    def get_category_id(self, category):
        """Get the id for a category

        Parameters
        ----------
        category : str
            The category name

        Returns
        -------
        int
            The category id
        """
        sql = "SELECT id FROM categories WHERE name = ?"
        self.cursor.execute(sql, (category,))

        return self.cursor.fetchone()[0]

    def get_organization_id(self, organization):
        """Get the id for a organization

        Parameters
        ----------
        organization : str
            The organization name

        Returns
        -------
        int
            The organization id
        """
        sql = "SELECT id FROM organizations WHERE name = ?"
        self.cursor.execute(sql, (organization,))

        return self.cursor.fetchone()[0]

    def get_repo_id(self, full_name, name=None):
        """Get the id for a repo

        Parameters
        ----------
        full_name : str
            The repo name as <organization/name> or just the organization if name is
            given separately
        name : str (optional)
            The name of the repo if the first argument is the organization

        Returns
        -------
        int
            The repo id
        """
        if name is not None:
            full_name += "/" + name

        sql = "SELECT id FROM repos WHERE full_name = ?"
        self.cursor.execute(sql, (full_name,))

        return self.cursor.fetchone()[0]

    def get_repo_topics(self, full_name, name=None):
        """Get the topics for a repo

        Parameters
        ----------
        full_name : str|int
            The repo name as <organization/name> or just the organization if name is
            given separately, or the id
        name : str (optional)
            The name of the repo if the first argument is the organization

        Returns
        -------
        [str]
            The list of topics for the repo
        """
        if isinstance(full_name, int):
            sql = (
                "SELECT t.name FROM topics as t, repos_topics as rt"
                " WHERE rt.repo = ? AND t.id = rt.topic"
            )
        else:
            if name is not None:
                full_name += "/" + name

            sql = (
                "SELECT t.name FROM repos as r, topics as t, repos_topics as rt"
                " WHERE r.full_name = ? AND rt.repo = r.id AND t.id = rt.topic"
            )
        self.cursor.execute(sql, (full_name,))

        rows = self.cursor.fetchall()

        if rows is None:
            result = []
        else:
            result = sorted([row[0] for row in rows])

        return result

    def get_topic_id(self, topic):
        """Get the id for a topic

        Parameters
        ----------
        topic : str
            The topic name

        Returns
        -------
        int
            The topic id
        """
        sql = "SELECT id FROM topics WHERE name = ?"
        self.cursor.execute(sql, (topic,))

        return self.cursor.fetchone()[0]

    def organization_exists(self, name):
        """See if the given organization exists in the database.

        Parameters
        ----------
        name : str
            The name of the organization.

        Returns
        -------
        bool
            Whether it exists.
        """
        sql = "SELECT COUNT(*) FROM organizations WHERE name = ?"
        self.cursor.execute(sql, (name,))

        return self.cursor.fetchone()[0] != 0

    def repo_exists(self, full_name, name=None):
        """See if the given repo exists in the database.

        Parameters
        ----------
        full_name : str
            The repo name as <organization/name> or just the organization if name is
            given separately
        name : str (optional)
            The name of the repo if the first argument is the organization

        Returns
        -------
        bool
            Whether it exists.
        """
        if name is not None:
            full_name += "/" + name

        sql = "SELECT COUNT(*) FROM repos WHERE full_name = ?"
        self.cursor.execute(sql, (full_name,))

        return self.cursor.fetchone()[0] != 0

    def topic_exists(self, topic):
        """See if the given topic exists in the database.

        Parameters
        ----------
        topic : str
            The name of the topic

        Returns
        -------
        bool
            Whether it exists.
        """
        sql = "SELECT COUNT(*) FROM topics WHERE name = ?"
        self.cursor.execute(sql, (topic,))

        return self.cursor.fetchone()[0] != 0
