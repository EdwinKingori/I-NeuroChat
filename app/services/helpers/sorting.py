from sqlalchemy import asc, desc

def apply_sorting(
    query, 
    model, 
    sort_by:str, 
    order:str,
):
    """
    Safe sorting with attribute listing
    """
    if not hasattr(model, sort_by):
        return query
    
    column = getattr(model, sort_by)
    
    if order.lower() == "desc":
        return query.order_by(desc(column))
    
    return query.order_by(asc(column))