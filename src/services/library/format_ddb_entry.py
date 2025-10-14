from typing import Optional
from mypy_boto3_dynamodb.type_defs import AttributeValueTypeDef
from pydantic import BaseModel, Field

from boto3.dynamodb.types import TypeDeserializer, TypeSerializer
from services.library.get_s3_presigned_url import get_s3_presigned_url

ddb_deserializer = TypeDeserializer()
ddb_serializer = TypeSerializer()

class DdbTitleItem(BaseModel):
    '''
    Raw ddb title item post-deserialization.
    '''
    PK: str = Field(pattern=r'^USER#')
    SK: str = Field(pattern=r'^TITLE#')

    title: str
    author: str
    date_published: str
    date_downloaded: str
    num_of_pages: int

    pdf_link: str # Uri
    parsed_pdf_link: str # Uri

    notes: list
    last_viewed: Optional[str] = None

class Title(BaseModel):
    '''
    Title object for API responses.
    '''
    id: str
    title: str
    author: str
    pages: int
    date_published: str
    date_downloaded: str

    # Dne until get_s3_presigned is called.
    pdf_presigned_url: str | None = None
    parsed_pdf_presigned_url: str | None = None
    #

    notes: list
    last_viewed: Optional[str] = None

def deserialize_ddb_title_item(ddb_book_item: dict[str, AttributeValueTypeDef]) -> tuple[Title, DdbTitleItem]:
    item = {k: ddb_deserializer.deserialize(v) for k, v in ddb_book_item.items()}
    
    ddb_title_item = DdbTitleItem(**item)
    
    pdf_s3_key = ddb_title_item.pdf_link.split('/', 3)[-1]
    parsed_pdf_s3_key = ddb_title_item.parsed_pdf_link.split('/', 3)[-1]

    
    title = Title(
        id=ddb_title_item.SK.partition("#")[2],
        title=ddb_title_item.title,
        author=ddb_title_item.author,

        date_published=ddb_title_item.date_published,
        date_downloaded=ddb_title_item.date_downloaded,

        pdf_presigned_url=get_s3_presigned_url(pdf_s3_key),
        parsed_pdf_presigned_url=get_s3_presigned_url(parsed_pdf_s3_key),

        pages=ddb_title_item.num_of_pages,
        notes=ddb_title_item.notes
    )

    return title, ddb_title_item

def serialize_title(title: Title, sub: str, pdf_s3_uri: str, parsed_pdf_s3_uri: str ) -> dict[str, AttributeValueTypeDef]:
    book_item = DdbTitleItem(
        PK=f"USER#{sub}",
        SK=f"TITLE#{title.id}",

        title=title.title,
        author=title.author,
        date_published=title.date_published,
        date_downloaded=title.date_downloaded,

        pdf_link=pdf_s3_uri,
        parsed_pdf_link=parsed_pdf_s3_uri,

        num_of_pages=title.pages,
        notes=title.notes
    )
    
    return {k: ddb_serializer.serialize(v) for k, v in book_item.model_dump().items()}
