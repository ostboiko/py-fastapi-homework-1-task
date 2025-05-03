from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db, MovieModel
from schemas import MovieDetailResponseSchema, MovieListResponseSchema

router = APIRouter()

@router.get(
    "/movies/",
    response_model=MovieListResponseSchema
)
async def get_movies(
        page: int = Query(1, ge=1),
        per_page: int = Query(10, ge=1, le=20),
        db: AsyncSession = Depends(get_db),
) -> MovieListResponseSchema:
    query = select(MovieModel).limit(per_page).offset((page - 1) * per_page)
    result = await db.execute(query)
    movies_list = result.scalars().all()

    if not movies_list:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No movies found."
        )

    movies = [MovieDetailResponseSchema.from_orm(movie)
              for movie in movies_list]

    count_query = select(func.count()).select_from(MovieModel)
    count_result = await db.execute(count_query)

    total_items = count_result.scalar()
    total_pages = ceil(total_items / per_page)

    if page == 1:
        prev_page = None
    else:
        prev_page = f"/theater/movies/?page={page - 1}&per_page={per_page}"

    if page == total_pages:
        next_page = None
    else:
        next_page = f"/theater/movies/?page={page + 1}&per_page={per_page}"

    response = MovieListResponseSchema(
        movies=movies,
        prev_page=prev_page,
        next_page=next_page,
        total_pages=total_pages,
        total_items=total_items
    )
    return response


@router.get(
    "/movies/{film_id}/",
    response_model=MovieDetailResponseSchema
)
async def get_movie(
        film_id: int,
        db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(MovieModel).where(MovieModel.id == film_id)
    )
    movie = result.scalar_one_or_none()
    if not movie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie with the given ID was not found."
        )
    return MovieDetailResponseSchema.from_orm(movie)
