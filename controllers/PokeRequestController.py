import json
import logging

from fastapi import HTTPException, Response
from models.PokeRequest import PokemonRequest
from utils.database import execute_query_json
from utils.AQueue import AQueue
from utils.ABlob import ABlob


# configurar el logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def select_pokemon_request(id: int):
    try:
        query = "select * from pokequeue.requests where id = ?"
        params = (id,)
        result = await execute_query_json(query, params)
        result_dict = json.loads(result)
        return result_dict
    except Exception as e:
        logger.error(f"Error selecting report request {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


async def update_pokemon_request(pokemon_request: PokemonRequest) -> dict:
    try:
        query = " exec pokequeue.update_poke_request ?, ?, ? "
        if not pokemon_request.url:
            pokemon_request.url = ""

        params = (pokemon_request.id, pokemon_request.status,
                  pokemon_request.url)
        result = await execute_query_json(query, params, True)
        result_dict = json.loads(result)
        return result_dict
    except Exception as e:
        logger.error(f"Error updating report request {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


async def insert_pokemon_request(pokemon_request: PokemonRequest) -> dict:
    try:
        if pokemon_request.sample_size:
            query = " exec pokequeue.create_poke_request ?, ?"
            params = (pokemon_request.pokemon_type,
                      pokemon_request.sample_size,)
        else:
            query = " exec pokequeue.create_poke_request ? "
            params = (pokemon_request.pokemon_type,)

        result = await execute_query_json(query, params, True)
        result_dict = json.loads(result)

        await AQueue().insert_message_on_queue(result)

        return result_dict
    except Exception as e:
        logger.error(f"Error inserting report request {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


async def get_all_request() -> dict:
    query = """
        SELECT
            r.id as ReportId, 
            s.description as Status, 
            r.type as PokemonType, 
            r.url, 
            r.created, 
            r.updated,
            r.sample_size
        FROM pokequeue.requests r
        JOIN pokequeue.status s ON r.id_status = s.id
    """
    result = await execute_query_json(query)
    result_dict = json.loads(result)
    blob = ABlob()
    for record in result_dict:
        id = record['ReportId']
        record['url'] = f"{record['url']}?{blob.generate_sas(id)}"
    return result_dict


async def delete_poke_request(id: int):
    try:
        # Definiendo Query para la búsqueda del request en la DB
        query = "SELECT 1 FROM pokequeue.requests r WHERE r.id = ?"
        params = (id, )

        # Buscando request en la BD
        findRequest = await execute_query_json(query, params)
        result_dict = json.loads(findRequest)

        # Si la request no existe, se lanza un error 404
        if len(result_dict) == 0:
            raise HTTPException(
                status_code=404, detail=f"Report with ID '{id}' not found")

        # Definiendo Query para eliminar el request y ejecutándola
        query = "DELETE FROM pokequeue.requests WHERE id = ?"
        await execute_query_json(query, params, needs_commit=True)

        # Eliminacion del reporte
        blob = ABlob()
        try:
            blob.delete_blob(id)
        except Exception as blob_err:
            logger.warning(
                f"No se pudo eliminar el blob asociado al reporte {id}: {blob_err}")

        return Response(status_code=204)
    except Exception as e:
        logger.error(f"Error deleting report")
        if isinstance(e, HTTPException) and e.status_code == 404:
            raise e
        raise HTTPException(status_code=500, detail="Internal server error")
