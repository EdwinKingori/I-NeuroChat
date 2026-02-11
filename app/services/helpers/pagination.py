from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

async def paginate_query(
    *,
    session: AsyncSession,
    query,
    page: int=1,
    limit:int=20,
):
    """
    Generic pagination helper.

    Returns:
    - items
    - total_count
    """
    offset = (page-1)*limit

    count_query = select(func.count()).select_from(query.subquery())
    total = await session.scalar(count_query)

    result = await session.execute(
        query.limit(limit).offset(offset)
    )

    return result.scalars().all(), total