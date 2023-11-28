import random

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlmodel import Session, select

from src.config.database import get_session
from src.models.reservas_model import Reserva
from src.models.voos_model import Voo

reservas_router = APIRouter(prefix="/reservas")


@reservas_router.get("/{id_voo}")
def lista_reservas_voo(id_voo: int):
    with get_session() as session:
        statement = select(Reserva).where(Reserva.voo_id == id_voo)
        reservas = session.exec(statement).all()
        return reservas


@reservas_router.post("")
def cria_reserva(reserva: Reserva):
    with get_session() as session:
        voo = session.exec(select(Voo).where(Voo.id == reserva.voo_id)).first()

        if not voo:
            return JSONResponse(
                content={"message": f"Voo com id {reserva.voo_id} não encontrado."},
                status_code=404,
            )

        # TODO - Validar se existe uma reserva para o mesmo documento
        reserva_existente = session.exec(
            select(Reserva)
            .where(Reserva.documento == reserva.documento)
            .where(Reserva.voo_id == reserva.voo_id)
        ).first()

        if reserva_existente:
            return JSONResponse(
                content={"message": f"Já existe uma reserva para o número de documento {reserva.documento} neste voo."},
                status_code=400,
            )

        codigo_reserva = "".join(
            [str(random.randint(0, 999)).zfill(3) for _ in range(2)]
        )

        reserva.codigo_reserva = codigo_reserva
        session.add(reserva)
        session.commit()
        session.refresh(reserva)
        return reserva

@reservas_router.post("/{codigo_reserva}/checkin/{num_poltrona}")
def faz_checkin(codigo_reserva: str, num_poltrona: int, session: Session = Depends(get_session)):
    with session.begin():
       
        reserva = session.exec(select(Reserva).where(Reserva.codigo_reserva == codigo_reserva)).first()

        if not reserva:
            raise HTTPException(
                status_code=404,
                detail=f"Reserva com código {codigo_reserva} não encontrada."
            )

        
        if reserva.status == "confirmada":
            raise HTTPException(
                status_code=400,
                detail="Reserva já confirmada, não é possível fazer check-in novamente."
            )

        
        if num_poltrona < 1 or num_poltrona > reserva.voo.numero_poltronas:
            raise HTTPException(
                status_code=400,
                detail=f"Número de poltrona inválido para o voo associado à reserva."
            )

        if num_poltrona in [r.num_poltrona for r in reserva.voo.reservas if r.status == "confirmada"]:
            raise HTTPException(
                status_code=400,
                detail=f"Poltrona {num_poltrona} já ocupada."
            )

       
        reserva.status = "confirmada"
        reserva.num_poltrona = num_poltrona

        session.commit()
        session.refresh(reserva)

    return reserva
@reservas_router.patch("/{voo_id}/checkin/{num_poltrona}")
def faz_checkin(voo_id: int, num_poltrona: int, session: Session = Depends(get_session)):
    with session.begin():
        
        reserva = session.query(Reserva).filter_by(id=voo_id).first()

        if not reserva:
            raise HTTPException(
                status_code=404,
                detail="Reserva não encontrada."
            )

        
        if reserva.status == "confirmada":
            raise HTTPException(
                status_code=400,
                detail="Reserva já confirmada, não é possível fazer check-in novamente."
            )

        
        if num_poltrona < 1 or num_poltrona > reserva.voo.numero_poltronas:
            raise HTTPException(
                status_code=400,
                detail=f"Número de poltrona inválido para o voo associado à reserva."
            )

        
        if num_poltrona in [r.num_poltrona for r in reserva.voo.reservas if r.status == "confirmada"]:
            raise HTTPException(
                status_code=403,
                detail="Poltrona ocupada."
            )

        
        reserva.status = "confirmada"
        reserva.num_poltrona = num_poltrona

        session.commit()
        session.refresh(reserva)

    return reserva