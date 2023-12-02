from pydantic import BaseModel
from typing import List

class User(BaseModel):
    """Item defining a scraped user profile."""

    user_id: int
    user_name: str

class QuoteData(BaseModel):
    """Defining data model for quote (meta) data."""

    author_name: str
    author_page: str
    avatar_img: str
    quote: str
    num_likes: int 
    feed_url: str 
    tags: List[str]
    liking_users: List[User]

class Quote(BaseModel):
    """Item defining a scraped quote."""

    id: int
    data: QuoteData
