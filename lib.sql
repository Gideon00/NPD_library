CREATE TABLE "users" (
    "id" INTEGER,
    "name" TEXT NOT NULL,
    "username" TEXT NOT NULL UNIQUE,
    "mail" TEXT,
    "hash" TEXT NOT NULL,
    "date_joined" NUMERIC NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY("id")
);

CREATE TABLE "authored" (
    "author_id" INTEGER,
    "book_id" INTEGER,
    FOREIGN KEY("author_id") REFERENCES "authors"("id") ON DELETE CASCADE,
    FOREIGN KEY("book_id") REFERENCES "books"("id") ON DELETE CASCADE
);

CREATE TABLE "authors" (
    "id" INTEGER,
    "name" TEXT NOT NULL,
    "country" TEXT,
    "birth" NUMERIC,
    PRIMARY KEY("id")
);

CREATE TABLE "books" (
    "id" INTEGER,
    "isbn" TEXT,
    "title" TEXT NOT NULL,
    "year" NUMERIC,
    "publisher_id" INTEGER,
    "pages" INTEGER NOT NULL,
    "date_uploaded" NUMERIC NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY("id"),
    FOREIGN KEY("publisher_id") REFERENCES "publishers"("id")
);

CREATE TABLE "publishers" (
    "id" INTEGER,
    "publisher" TEXT,
    PRIMARY KEY("id")
);

CREATE TABLE "files" (
    "book_id" INTEGER,
    "book_path" TEXT NOT NULL,
    "book_img_path" TEXT NOT NULL,
    FOREIGN KEY("book_id") REFERENCES "books"("id") ON DELETE CASCADE
);

CREATE TABLE "recommendations" (
    "user_id" INTEGER,
    "recommendation" TEXT NOT NULL,
    "datetime" NUMERIC NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY("user_id") REFERENCES "users"("id") ON DELETE CASCADE
);

CREATE TABLE "admins" (
    "id" INTEGER,
    "user_id" INTEGER,
    "datetime" NUMERIC NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY("id"),
    FOREIGN KEY("user_id") REFERENCES "users"("id") ON DELETE CASCADE
);

CREATE VIEW "longlist" AS
SELECT
    b.id AS book_id,
    b.isbn,
    b.title AS book_title,
    b.year AS book_year,
    p.publisher AS publisher_name,
    b.pages,
    b.date_uploaded,
    f.book_path,
    f.book_img_path,
    GROUP_CONCAT(a.id) AS author_ids,
    GROUP_CONCAT(a.name) AS author_names,
    GROUP_CONCAT(a.country) AS author_countries,
    GROUP_CONCAT(a.birth) AS author_births,
    GROUP_CONCAT((strftime('%Y', 'now') - strftime('%Y', a.birth)) - (strftime('%m-%d', 'now') < strftime('%m-%d', a.birth))) AS author_ages
FROM
    authors a
JOIN
    authored au ON a.id = au.author_id
JOIN
    books b ON au.book_id = b.id
LEFT JOIN
    publishers p ON b.publisher_id = p.id
LEFT JOIN
    files f ON b.id = f.book_id
GROUP BY
    b.id;

CREATE VIEW "suggestions" AS
SELECT
    u.id AS user_id,
    u.username AS user_username,
    r.recommendation,
    r.datetime
FROM
    users u
JOIN
    recommendations r ON u.id = r.user_id;