import boto3
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from importlib import reload
from moto import mock_aws

REGION = "us-east-1"
TABLE_NAME = "testtable"
BUCKET_NAME = "test-bucket"
SUB = "user-123"

# --- Ensure env is set and no real AWS creds leak into boto3 ---
@pytest.fixture(autouse=True)
def settings_env(monkeypatch):
    for k in ("AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_SESSION_TOKEN"):
        monkeypatch.delenv(k, raising=False)
    monkeypatch.setenv("REGION", REGION)
    monkeypatch.setenv("DDB_TABLE_NAME", TABLE_NAME)
    monkeypatch.setenv("BUCKET_NAME", BUCKET_NAME)
    monkeypatch.setenv("SUB", SUB)
    yield

# --- Start Moto BEFORE importing modules that create boto3 clients at import time ---
@pytest.fixture
def moto_aws():
    with mock_aws():
        ddb = boto3.resource("dynamodb", region_name=REGION)
        table = ddb.create_table(
            TableName=TABLE_NAME,
            KeySchema=[{"AttributeName": "PK", "KeyType": "HASH"},
                       {"AttributeName": "SK", "KeyType": "RANGE"}],
            AttributeDefinitions=[
                {"AttributeName": "PK", "AttributeType": "S"},
                {"AttributeName": "SK", "AttributeType": "S"},
            ],
            BillingMode="PAY_PER_REQUEST",
        )
        table.wait_until_exists()

        s3 = boto3.client("s3", region_name=REGION)
        s3.create_bucket(Bucket=BUCKET_NAME)

        yield {"ddb": ddb, "table": table, "s3": s3}

# --- Build the FastAPI app the same way your real server does ---
@pytest.fixture
def app(moto_aws, monkeypatch):
    # Reload modules AFTER Moto so module-level boto3 clients bind to Moto
    import api.v1.endpoints.library as lib
    reload(lib)

    # Your get_titles_all() requires a verified sub; stub it
    monkeypatch.setattr(lib, "verify_token", lambda _hdr: SUB)

    from api.v1 import api as v1
    reload(v1)

    a = FastAPI()
    a.include_router(v1.router, prefix="/api/v1")
    return a

@pytest.fixture
def client(app):
    return TestClient(app)

@pytest.fixture
def seed_ddb(moto_aws):
    table = moto_aws["table"]
    test_books = [
    {
        "SK": "BOOK#Dune",
        "title": "Dune",
        "author": "Frank Herbert",
        "date_published": "1965-06-01",
        "num_of_pages": 688,
    },
    {
        "SK": "BOOK#1984",
        "title": "1984",
        "author": "George Orwell",
        "date_published": "1949-06-08",
        "num_of_pages": 328,
    },
    {
        "SK": "BOOK#BraveNewWorld",
        "title": "Brave New World",
        "author": "Aldous Huxley",
        "date_published": "1932-01-01",
        "num_of_pages": 311,
    },
    {
        "SK": "BOOK#Fahrenheit451",
        "title": "Fahrenheit 451",
        "author": "Ray Bradbury",
        "date_published": "1953-10-19",
        "num_of_pages": 249,
    },
    {
        "SK": "BOOK#Foundation",
        "title": "Foundation",
        "author": "Isaac Asimov",
        "date_published": "1951-06-01",
        "num_of_pages": 255,
    },
    {
        "SK": "BOOK#TheHobbit",
        "title": "The Hobbit",
        "author": "J.R.R. Tolkien",
        "date_published": "1937-09-21",
        "num_of_pages": 310,
    },
    {
        "SK": "BOOK#ToKillAMockingbird",
        "title": "To Kill a Mockingbird",
        "author": "Harper Lee",
        "date_published": "1960-07-11",
        "num_of_pages": 281,
    },
    {
        "SK": "BOOK#TheMartian",
        "title": "The Martian",
        "author": "Andy Weir",
        "date_published": "2011-02-11",
        "num_of_pages": 369,
    },
    {
        "SK": "BOOK#Neuromancer",
        "title": "Neuromancer",
        "author": "William Gibson",
        "date_published": "1984-07-01",
        "num_of_pages": 271,
    },
    {
        "SK": "BOOK#SnowCrash",
        "title": "Snow Crash",
        "author": "Neal Stephenson",
        "date_published": "1992-06-01",
        "num_of_pages": 470,
    },
    ]

    for book in test_books:
        table.put_item(
            Item={
                 "PK": f"USER#{SUB}",
                "SK": book["SK"],
                "title": book["title"],
                "author": book["author"],
                "date_published": book["date_published"],
                "date_downloaded": "2025-10-03T12:00:00Z",
                "pdf_link": f"s3://{BUCKET_NAME}/user/{SUB}/{book['title'].replace(' ', '_')}.pdf",
                "num_of_pages": book["num_of_pages"],
                "notes": [],
            }
        )

   
    return table

def test_list_books_reads_from_ddb(client, seed_ddb, app):
    url = "/api/v1/library/get-titles-all/"  
    resp = client.get(url, headers={"Authorization": "Bearer test"})
    assert resp.status_code == 200
    data = resp.json()
    titles = [b["title"] for b in data]
    assert "Neuromancer" in titles

def test_singular_book_retrieval(client, seed_ddb, app):
    url = "/api/v1/library/get-title/"   
    resp = client.get(url, headers={"Authorization": "Bearer test"}, params={"title_name": "Dune"})
    assert resp.status_code == 200
    data = resp.json()
    assert data['book']['title'] == "Dune"

def test_delete_book(client, seed_ddb, app):
    url = "/api/v1/library/delete-title/"
    resp = client.delete(url, headers={"Authorization": "Bearer test"}, params={"title_name": "Dune"})
    assert resp.status_code == 200
    
    #final verification (return all titles and make sure the deleted file not present)
    url = "/api/v1/library/get-titles-all/"   
    resp = client.get(url, headers={"Authorization": "Bearer test"})
    data = resp.json()
    titles = [b["title"] for b in data]
    assert resp.status_code == 200 and "Dune" not in titles