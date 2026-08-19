"""Modèles de base de données pour l'exploitation végétale.

Toutes les entités persistantes de l'application partagent la même `Base`
SQLAlchemy déclarative. Aucune requête applicative ni composant visuel ici.
"""

from __future__ import annotations

import datetime
import enum

from sqlalchemy import (
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    MappedAsDataclass,
    mapped_column,
    relationship,
)


class Base(MappedAsDataclass, DeclarativeBase, kw_only=True):
    """Base déclarative unique pour toute l'application."""


# ---------------------------------------------------------------------------
# Énumérations métier
# ---------------------------------------------------------------------------


class SoilType(str, enum.Enum):
    ARGILEUX = "argileux"
    LIMONEUX = "limoneux"
    SABLEUX = "sableux"
    ARGILO_CALCAIRE = "argilo_calcaire"
    LIMONO_SABLEUX = "limono_sableux"
    HUMIFERE = "humifere"
    AUTRE = "autre"


class IrrigationType(str, enum.Enum):
    AUCUNE = "aucune"
    ASPERSION = "aspersion"
    GOUTTE_A_GOUTTE = "goutte_a_goutte"
    PIVOT = "pivot"
    GRAVITAIRE = "gravitaire"


class ParcelStatus(str, enum.Enum):
    EN_CULTURE = "en_culture"
    JACHERE = "jachere"
    PREPARATION = "preparation"
    RECOLTEE = "recoltee"
    INACTIVE = "inactive"


class CropStage(str, enum.Enum):
    SEMIS = "semis"
    LEVEE = "levee"
    TALLAGE = "tallage"
    CROISSANCE = "croissance"
    FLORAISON = "floraison"
    FRUCTIFICATION = "fructification"
    MATURATION = "maturation"
    RECOLTE = "recolte"
    TERMINEE = "terminee"


class CropStatus(str, enum.Enum):
    PLANIFIEE = "planifiee"
    EN_COURS = "en_cours"
    RECOLTEE = "recoltee"
    ABANDONNEE = "abandonnee"


class HealthLevel(str, enum.Enum):
    EXCELLENT = "excellent"
    BON = "bon"
    MOYEN = "moyen"
    FAIBLE = "faible"
    CRITIQUE = "critique"


class InterventionType(str, enum.Enum):
    SEMIS = "semis"
    PLANTATION = "plantation"
    FERTILISATION = "fertilisation"
    TRAITEMENT_PHYTO = "traitement_phyto"
    DESHERBAGE = "desherbage"
    IRRIGATION = "irrigation"
    TRAVAIL_DU_SOL = "travail_du_sol"
    OBSERVATION = "observation"
    RECOLTE = "recolte"
    AUTRE = "autre"


class InterventionStatus(str, enum.Enum):
    PLANIFIEE = "planifiee"
    EN_COURS = "en_cours"
    REALISEE = "realisee"
    ANNULEE = "annulee"
    REPORTEE = "reportee"


class ProductCategory(str, enum.Enum):
    ENGRAIS = "engrais"
    FONGICIDE = "fongicide"
    HERBICIDE = "herbicide"
    INSECTICIDE = "insecticide"
    SEMENCE = "semence"
    AMENDEMENT = "amendement"
    BIOSTIMULANT = "biostimulant"
    AUTRE = "autre"


class StockMovementType(str, enum.Enum):
    ENTREE = "entree"
    SORTIE = "sortie"
    INVENTAIRE = "inventaire"
    PERTE = "perte"


class AlertLevel(str, enum.Enum):
    INFO = "info"
    ATTENTION = "attention"
    CRITIQUE = "critique"


class HarvestQuality(str, enum.Enum):
    A = "a"
    B = "b"
    C = "c"
    DECLASSEE = "declassee"


class EmployeeStatus(str, enum.Enum):
    ACTIF = "actif"
    CONGE = "conge"
    ARRET_MALADIE = "arret_maladie"
    FORMATION = "formation"
    SORTI = "sorti"


class ContractType(str, enum.Enum):
    CDI = "cdi"
    CDD = "cdd"
    SAISONNIER = "saisonnier"
    APPRENTI = "apprenti"
    STAGE = "stage"
    PRESTATAIRE = "prestataire"


class SkillLevel(str, enum.Enum):
    DEBUTANT = "debutant"
    INTERMEDIAIRE = "intermediaire"
    AVANCE = "avance"
    EXPERT = "expert"


class AvailabilityType(str, enum.Enum):
    DISPONIBLE = "disponible"
    CONGE = "conge"
    ARRET = "arret"
    FORMATION = "formation"
    ASTREINTE = "astreinte"
    INDISPONIBLE = "indisponible"


class AssignmentStatus(str, enum.Enum):
    PROPOSEE = "proposee"
    CONFIRMEE = "confirmee"
    EN_COURS = "en_cours"
    TERMINEE = "terminee"
    ANNULEE = "annulee"


class AssignmentRole(str, enum.Enum):
    RESPONSABLE = "responsable"
    CONDUCTEUR = "conducteur"
    OPERATEUR = "operateur"
    AIDE = "aide"
    OBSERVATEUR = "observateur"


class EquipmentCategory(str, enum.Enum):
    TRACTEUR = "tracteur"
    MOISSONNEUSE = "moissonneuse"
    PULVERISATEUR = "pulverisateur"
    SEMOIR = "semoir"
    OUTIL_TRAVAIL_SOL = "outil_travail_sol"
    REMORQUE = "remorque"
    IRRIGATION = "irrigation"
    MANUTENTION = "manutention"
    VEHICULE = "vehicule"
    AUTRE = "autre"


class EquipmentStatus(str, enum.Enum):
    DISPONIBLE = "disponible"
    EN_SERVICE = "en_service"
    EN_MAINTENANCE = "en_maintenance"
    HORS_SERVICE = "hors_service"
    RESERVE = "reserve"
    CEDE = "cede"


class OwnershipType(str, enum.Enum):
    PROPRIETE = "propriete"
    LEASING = "leasing"
    LOCATION = "location"
    COPROPRIETE = "copropriete"
    PRESTATION = "prestation"


class UsageUnit(str, enum.Enum):
    HEURES = "heures"
    KILOMETRES = "kilometres"
    HECTARES = "hectares"


class MaintenanceKind(str, enum.Enum):
    PREVENTIVE = "preventive"
    CORRECTIVE = "corrective"
    REGLEMENTAIRE = "reglementaire"
    AMELIORATION = "amelioration"


class MaintenanceStatus(str, enum.Enum):
    PLANIFIEE = "planifiee"
    EN_COURS = "en_cours"
    REALISEE = "realisee"
    REPORTEE = "reportee"
    ANNULEE = "annulee"


class MaintenancePriority(str, enum.Enum):
    BASSE = "basse"
    NORMALE = "normale"
    HAUTE = "haute"
    URGENTE = "urgente"


class MaintenanceCostType(str, enum.Enum):
    PIECE = "piece"
    MAIN_OEUVRE = "main_oeuvre"
    CONSOMMABLE = "consommable"
    SOUS_TRAITANCE = "sous_traitance"
    TRANSPORT = "transport"
    AUTRE = "autre"


class TriggerBasis(str, enum.Enum):
    CALENDRIER = "calendrier"
    COMPTEUR = "compteur"
    MIXTE = "mixte"


class ExpenseStatus(str, enum.Enum):
    BROUILLON = "brouillon"
    ENGAGEE = "engagee"
    PAYEE = "payee"
    ANNULEE = "annulee"


class PaymentMethod(str, enum.Enum):
    VIREMENT = "virement"
    PRELEVEMENT = "prelevement"
    CARTE = "carte"
    CHEQUE = "cheque"
    ESPECES = "especes"
    AUTRE = "autre"


class GeometrySource(str, enum.Enum):
    """Origine de la géométrie cartographique d'une parcelle."""

    AUCUNE = "aucune"
    GENEREE = "generee"
    DESSINEE = "dessinee"
    IMPORTEE = "importee"
    CADASTRE = "cadastre"


# ---------------------------------------------------------------------------
# Référentiels
# ---------------------------------------------------------------------------


class CropVariety(Base):
    """Référentiel des espèces/variétés cultivables."""

    __tablename__ = "crop_variety"
    __table_args__ = (
        UniqueConstraint("species", "name", name="uq_variety_species_name"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    name: Mapped[str] = mapped_column(String(120))
    species: Mapped[str] = mapped_column(String(120))
    family: Mapped[str] = mapped_column(String(120), default="")
    cycle_days: Mapped[int] = mapped_column(default=0)
    expected_yield_t_ha: Mapped[float] = mapped_column(
        Numeric(10, 2), default=0
    )
    sowing_window: Mapped[str] = mapped_column(String(80), default="")
    harvest_window: Mapped[str] = mapped_column(String(80), default="")
    color_hex: Mapped[str] = mapped_column(String(9), default="#4ade80")
    icon: Mapped[str] = mapped_column(String(40), default="sprout")
    notes: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), init=False
    )

    crops: Mapped[list["Crop"]] = relationship(
        back_populates="variety", default_factory=list, repr=False
    )


class Product(Base):
    """Produit d'intrant (engrais, phyto, semence...) et son stock courant."""

    __tablename__ = "product"

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    name: Mapped[str] = mapped_column(String(160))
    category: Mapped[ProductCategory] = mapped_column(
        Enum(ProductCategory, native_enum=False, length=32),
        default=ProductCategory.AUTRE,
    )
    supplier: Mapped[str] = mapped_column(String(160), default="")
    reference: Mapped[str] = mapped_column(String(80), default="")
    active_substance: Mapped[str] = mapped_column(String(200), default="")
    unit: Mapped[str] = mapped_column(String(20), default="L")
    unit_price: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    quantity_in_stock: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    reorder_threshold: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    storage_location: Mapped[str] = mapped_column(String(120), default="")
    reentry_delay_hours: Mapped[int] = mapped_column(default=0)
    preharvest_delay_days: Mapped[int] = mapped_column(default=0)
    is_organic_approved: Mapped[bool] = mapped_column(default=False)
    expiry_date: Mapped[datetime.date | None] = mapped_column(
        Date, default=None
    )
    notes: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), init=False
    )

    movements: Mapped[list["StockMovement"]] = relationship(
        back_populates="product", default_factory=list, repr=False
    )
    intervention_products: Mapped[list["InterventionProduct"]] = relationship(
        back_populates="product", default_factory=list, repr=False
    )


# ---------------------------------------------------------------------------
# Parcelles & cultures
# ---------------------------------------------------------------------------


class Parcel(Base):
    """Parcelle agricole de l'exploitation."""

    __tablename__ = "parcel"

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    name: Mapped[str] = mapped_column(String(120))
    code: Mapped[str] = mapped_column(String(40), default="")
    area_ha: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    soil_type: Mapped[SoilType] = mapped_column(
        Enum(SoilType, native_enum=False, length=32), default=SoilType.LIMONEUX
    )
    irrigation: Mapped[IrrigationType] = mapped_column(
        Enum(IrrigationType, native_enum=False, length=32),
        default=IrrigationType.AUCUNE,
    )
    status: Mapped[ParcelStatus] = mapped_column(
        Enum(ParcelStatus, native_enum=False, length=32),
        default=ParcelStatus.PREPARATION,
    )
    locality: Mapped[str] = mapped_column(String(160), default="")
    latitude: Mapped[float] = mapped_column(Numeric(9, 6), default=0)
    longitude: Mapped[float] = mapped_column(Numeric(9, 6), default=0)
    # Position et taille relatives pour la carte stylisée du tableau de bord
    map_x: Mapped[float] = mapped_column(Numeric(6, 2), default=0)
    map_y: Mapped[float] = mapped_column(Numeric(6, 2), default=0)
    map_w: Mapped[float] = mapped_column(Numeric(6, 2), default=20)
    map_h: Mapped[float] = mapped_column(Numeric(6, 2), default=20)
    slope_percent: Mapped[float] = mapped_column(Numeric(5, 2), default=0)
    ph: Mapped[float] = mapped_column(Numeric(4, 2), default=7)
    organic_matter_percent: Mapped[float] = mapped_column(
        Numeric(5, 2), default=0
    )
    is_organic: Mapped[bool] = mapped_column(default=False)
    notes: Mapped[str] = mapped_column(Text, default="")
    # --- Géométrie cartographique persistante (carte réelle) -------------
    # Toutes ces colonnes sont NULLABLES et pourvues d'un `server_default` :
    # elles peuvent donc être ajoutées à une table déjà peuplée sans bloquer
    # la migration sur les lignes existantes.
    # Contour de la parcelle au format GeoJSON (Polygon ou MultiPolygon),
    # sérialisé en texte pour rester portable sans extension PostGIS.
    boundary_geojson: Mapped[str | None] = mapped_column(
        Text, nullable=True, server_default="", default=""
    )
    # Centre cartographique utilisé pour recentrer la carte sur la parcelle.
    center_lat: Mapped[float | None] = mapped_column(
        Numeric(9, 6), nullable=True, server_default="0", default=0
    )
    center_lon: Mapped[float | None] = mapped_column(
        Numeric(9, 6), nullable=True, server_default="0", default=0
    )
    map_zoom: Mapped[float | None] = mapped_column(
        Numeric(4, 1), nullable=True, server_default="15", default=15
    )
    # Emprise (bounding box) du contour, pratique pour un fitBounds direct.
    bbox_min_lat: Mapped[float | None] = mapped_column(
        Numeric(9, 6), nullable=True, server_default="0", default=0
    )
    bbox_min_lon: Mapped[float | None] = mapped_column(
        Numeric(9, 6), nullable=True, server_default="0", default=0
    )
    bbox_max_lat: Mapped[float | None] = mapped_column(
        Numeric(9, 6), nullable=True, server_default="0", default=0
    )
    bbox_max_lon: Mapped[float | None] = mapped_column(
        Numeric(9, 6), nullable=True, server_default="0", default=0
    )
    # Surface calculée depuis le contour, comparable à `area_ha` déclarée.
    geometry_area_ha: Mapped[float | None] = mapped_column(
        Numeric(10, 2), nullable=True, server_default="0", default=0
    )
    geometry_vertex_count: Mapped[int | None] = mapped_column(
        nullable=True, server_default="0", default=0
    )
    geometry_source: Mapped[GeometrySource | None] = mapped_column(
        Enum(GeometrySource, native_enum=False, length=32),
        nullable=True,
        server_default=GeometrySource.AUCUNE.name,
        default=GeometrySource.AUCUNE,
    )
    geometry_srid: Mapped[int | None] = mapped_column(
        nullable=True, server_default="4326", default=4326
    )
    geometry_color_hex: Mapped[str | None] = mapped_column(
        String(9), nullable=True, server_default="#a3e635", default="#a3e635"
    )
    geometry_updated_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )
    geometry_updated_by: Mapped[str | None] = mapped_column(
        String(120), nullable=True, server_default="", default=""
    )
    geometry_notes: Mapped[str | None] = mapped_column(
        Text, nullable=True, server_default="", default=""
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), init=False
    )

    crops: Mapped[list["Crop"]] = relationship(
        back_populates="parcel", default_factory=list, repr=False
    )
    interventions: Mapped[list["Intervention"]] = relationship(
        back_populates="parcel", default_factory=list, repr=False
    )
    soil_analyses: Mapped[list["SoilAnalysis"]] = relationship(
        back_populates="parcel", default_factory=list, repr=False
    )
    alerts: Mapped[list["Alert"]] = relationship(
        back_populates="parcel", default_factory=list, repr=False
    )


class Crop(Base):
    """Culture implantée sur une parcelle pour une campagne donnée."""

    __tablename__ = "crop"

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    parcel_id: Mapped[int] = mapped_column(
        ForeignKey("parcel.id", ondelete="CASCADE")
    )
    variety_id: Mapped[int | None] = mapped_column(
        ForeignKey("crop_variety.id", ondelete="SET NULL"), default=None
    )
    name: Mapped[str] = mapped_column(String(160), default="")
    season: Mapped[str] = mapped_column(String(40), default="")
    stage: Mapped[CropStage] = mapped_column(
        Enum(CropStage, native_enum=False, length=32), default=CropStage.SEMIS
    )
    status: Mapped[CropStatus] = mapped_column(
        Enum(CropStatus, native_enum=False, length=32),
        default=CropStatus.PLANIFIEE,
    )
    health: Mapped[HealthLevel] = mapped_column(
        Enum(HealthLevel, native_enum=False, length=32), default=HealthLevel.BON
    )
    area_ha: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    sowing_date: Mapped[datetime.date | None] = mapped_column(
        Date, default=None
    )
    expected_harvest_date: Mapped[datetime.date | None] = mapped_column(
        Date, default=None
    )
    actual_harvest_date: Mapped[datetime.date | None] = mapped_column(
        Date, default=None
    )
    seed_density: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    expected_yield_t_ha: Mapped[float] = mapped_column(
        Numeric(10, 2), default=0
    )
    progress_percent: Mapped[int] = mapped_column(default=0)
    notes: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), init=False
    )

    parcel: Mapped["Parcel"] = relationship(
        back_populates="crops", default=None, repr=False
    )
    variety: Mapped["CropVariety | None"] = relationship(
        back_populates="crops", default=None, repr=False
    )
    interventions: Mapped[list["Intervention"]] = relationship(
        back_populates="crop", default_factory=list, repr=False
    )
    harvests: Mapped[list["Harvest"]] = relationship(
        back_populates="crop", default_factory=list, repr=False
    )
    stage_logs: Mapped[list["CropStageLog"]] = relationship(
        back_populates="crop", default_factory=list, repr=False
    )


class CropStageLog(Base):
    """Historique des stades phénologiques d'une culture."""

    __tablename__ = "crop_stage_log"

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    crop_id: Mapped[int] = mapped_column(
        ForeignKey("crop.id", ondelete="CASCADE")
    )
    stage: Mapped[CropStage] = mapped_column(
        Enum(CropStage, native_enum=False, length=32), default=CropStage.SEMIS
    )
    observed_on: Mapped[datetime.date | None] = mapped_column(
        Date, default=None
    )
    observer: Mapped[str] = mapped_column(String(120), default="")
    comment: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), init=False
    )

    crop: Mapped["Crop"] = relationship(
        back_populates="stage_logs", default=None, repr=False
    )


class SoilAnalysis(Base):
    """Analyse de sol rattachée à une parcelle."""

    __tablename__ = "soil_analysis"

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    parcel_id: Mapped[int] = mapped_column(
        ForeignKey("parcel.id", ondelete="CASCADE")
    )
    sampled_on: Mapped[datetime.date | None] = mapped_column(Date, default=None)
    ph: Mapped[float] = mapped_column(Numeric(4, 2), default=7)
    nitrogen_ppm: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    phosphorus_ppm: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    potassium_ppm: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    organic_matter_percent: Mapped[float] = mapped_column(
        Numeric(5, 2), default=0
    )
    laboratory: Mapped[str] = mapped_column(String(160), default="")
    notes: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), init=False
    )

    parcel: Mapped["Parcel"] = relationship(
        back_populates="soil_analyses", default=None, repr=False
    )


# ---------------------------------------------------------------------------
# Interventions & traitements
# ---------------------------------------------------------------------------


class Intervention(Base):
    """Intervention agronomique (traitement, fertilisation, irrigation...)."""

    __tablename__ = "intervention"

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    parcel_id: Mapped[int] = mapped_column(
        ForeignKey("parcel.id", ondelete="CASCADE")
    )
    crop_id: Mapped[int | None] = mapped_column(
        ForeignKey("crop.id", ondelete="SET NULL"), default=None
    )
    type: Mapped[InterventionType] = mapped_column(
        Enum(InterventionType, native_enum=False, length=32),
        default=InterventionType.OBSERVATION,
    )
    status: Mapped[InterventionStatus] = mapped_column(
        Enum(InterventionStatus, native_enum=False, length=32),
        default=InterventionStatus.PLANIFIEE,
    )
    title: Mapped[str] = mapped_column(String(200), default="")
    scheduled_date: Mapped[datetime.date | None] = mapped_column(
        Date, default=None
    )
    done_date: Mapped[datetime.date | None] = mapped_column(Date, default=None)
    operator: Mapped[str] = mapped_column(String(120), default="")
    equipment: Mapped[str] = mapped_column(String(160), default="")
    area_treated_ha: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    water_volume_l_ha: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    duration_hours: Mapped[float] = mapped_column(Numeric(6, 2), default=0)
    cost: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    weather_conditions: Mapped[str] = mapped_column(String(160), default="")
    temperature_c: Mapped[float] = mapped_column(Numeric(5, 2), default=0)
    wind_speed_kmh: Mapped[float] = mapped_column(Numeric(5, 2), default=0)
    target: Mapped[str] = mapped_column(String(160), default="")
    notes: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), init=False
    )

    parcel: Mapped["Parcel"] = relationship(
        back_populates="interventions", default=None, repr=False
    )
    crop: Mapped["Crop | None"] = relationship(
        back_populates="interventions", default=None, repr=False
    )
    products: Mapped[list["InterventionProduct"]] = relationship(
        back_populates="intervention", default_factory=list, repr=False
    )


class InterventionProduct(Base):
    """Produit appliqué lors d'une intervention (dose et quantité totale)."""

    __tablename__ = "intervention_product"

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    intervention_id: Mapped[int] = mapped_column(
        ForeignKey("intervention.id", ondelete="CASCADE")
    )
    product_id: Mapped[int] = mapped_column(
        ForeignKey("product.id", ondelete="CASCADE")
    )
    dose_per_ha: Mapped[float] = mapped_column(Numeric(12, 3), default=0)
    total_quantity: Mapped[float] = mapped_column(Numeric(12, 3), default=0)
    unit: Mapped[str] = mapped_column(String(20), default="L")
    cost: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    notes: Mapped[str] = mapped_column(Text, default="")

    intervention: Mapped["Intervention"] = relationship(
        back_populates="products", default=None, repr=False
    )
    product: Mapped["Product"] = relationship(
        back_populates="intervention_products", default=None, repr=False
    )


class StockMovement(Base):
    """Mouvement de stock d'un produit d'intrant."""

    __tablename__ = "stock_movement"

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    product_id: Mapped[int] = mapped_column(
        ForeignKey("product.id", ondelete="CASCADE")
    )
    type: Mapped[StockMovementType] = mapped_column(
        Enum(StockMovementType, native_enum=False, length=32),
        default=StockMovementType.ENTREE,
    )
    quantity: Mapped[float] = mapped_column(Numeric(12, 3), default=0)
    unit_price: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    movement_date: Mapped[datetime.date | None] = mapped_column(
        Date, default=None
    )
    reference: Mapped[str] = mapped_column(String(120), default="")
    intervention_id: Mapped[int | None] = mapped_column(
        ForeignKey("intervention.id", ondelete="SET NULL"), default=None
    )
    notes: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), init=False
    )

    product: Mapped["Product"] = relationship(
        back_populates="movements", default=None, repr=False
    )


# ---------------------------------------------------------------------------
# Récoltes
# ---------------------------------------------------------------------------


class Harvest(Base):
    """Récolte effectuée sur une culture."""

    __tablename__ = "harvest"

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    crop_id: Mapped[int] = mapped_column(
        ForeignKey("crop.id", ondelete="CASCADE")
    )
    harvest_date: Mapped[datetime.date | None] = mapped_column(
        Date, default=None
    )
    quantity: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    unit: Mapped[str] = mapped_column(String(20), default="t")
    area_harvested_ha: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    yield_t_ha: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    moisture_percent: Mapped[float] = mapped_column(Numeric(5, 2), default=0)
    quality: Mapped[HarvestQuality] = mapped_column(
        Enum(HarvestQuality, native_enum=False, length=32),
        default=HarvestQuality.A,
    )
    loss_percent: Mapped[float] = mapped_column(Numeric(5, 2), default=0)
    storage_location: Mapped[str] = mapped_column(String(120), default="")
    unit_price: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    revenue: Mapped[float] = mapped_column(Numeric(14, 2), default=0)
    operator: Mapped[str] = mapped_column(String(120), default="")
    notes: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), init=False
    )

    crop: Mapped["Crop"] = relationship(
        back_populates="harvests", default=None, repr=False
    )


# ---------------------------------------------------------------------------
# Alertes agronomiques
# ---------------------------------------------------------------------------


class Alert(Base):
    """Alerte agronomique liée à une parcelle ou à l'exploitation."""

    __tablename__ = "alert"

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    parcel_id: Mapped[int | None] = mapped_column(
        ForeignKey("parcel.id", ondelete="CASCADE"), default=None
    )
    level: Mapped[AlertLevel] = mapped_column(
        Enum(AlertLevel, native_enum=False, length=32), default=AlertLevel.INFO
    )
    title: Mapped[str] = mapped_column(String(200), default="")
    message: Mapped[str] = mapped_column(Text, default="")
    category: Mapped[str] = mapped_column(String(80), default="")
    is_resolved: Mapped[bool] = mapped_column(default=False)
    triggered_on: Mapped[datetime.date | None] = mapped_column(
        Date, default=None
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), init=False
    )

    parcel: Mapped["Parcel | None"] = relationship(
        back_populates="alerts", default=None, repr=False
    )


# ---------------------------------------------------------------------------
# Employés, compétences, disponibilités et affectations
# ---------------------------------------------------------------------------


class Employee(Base):
    """Salarié ou intervenant de l'exploitation."""

    __tablename__ = "employee"

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    first_name: Mapped[str] = mapped_column(String(80))
    last_name: Mapped[str] = mapped_column(String(80))
    employee_code: Mapped[str] = mapped_column(String(40), default="")
    job_title: Mapped[str] = mapped_column(String(120), default="")
    contract_type: Mapped[ContractType] = mapped_column(
        Enum(ContractType, native_enum=False, length=32),
        default=ContractType.CDI,
    )
    status: Mapped[EmployeeStatus] = mapped_column(
        Enum(EmployeeStatus, native_enum=False, length=32),
        default=EmployeeStatus.ACTIF,
    )
    email: Mapped[str] = mapped_column(String(160), default="")
    phone: Mapped[str] = mapped_column(String(40), default="")
    hired_on: Mapped[datetime.date | None] = mapped_column(Date, default=None)
    contract_end_on: Mapped[datetime.date | None] = mapped_column(
        Date, default=None
    )
    weekly_hours: Mapped[float] = mapped_column(Numeric(5, 2), default=35)
    hourly_cost: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    team: Mapped[str] = mapped_column(String(120), default="")
    has_driving_licence: Mapped[bool] = mapped_column(default=False)
    has_phyto_certificate: Mapped[bool] = mapped_column(default=False)
    phyto_certificate_expiry: Mapped[datetime.date | None] = mapped_column(
        Date, default=None
    )
    emergency_contact: Mapped[str] = mapped_column(String(160), default="")
    notes: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), init=False
    )

    skills: Mapped[list["EmployeeSkill"]] = relationship(
        back_populates="employee", default_factory=list, repr=False
    )
    availabilities: Mapped[list["EmployeeAvailability"]] = relationship(
        back_populates="employee", default_factory=list, repr=False
    )
    assignments: Mapped[list["Assignment"]] = relationship(
        back_populates="employee", default_factory=list, repr=False
    )


class Skill(Base):
    """Référentiel des compétences mobilisables sur l'exploitation."""

    __tablename__ = "skill"
    __table_args__ = (UniqueConstraint("name", name="uq_skill_name"),)

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    name: Mapped[str] = mapped_column(String(120))
    category: Mapped[str] = mapped_column(String(80), default="")
    description: Mapped[str] = mapped_column(Text, default="")
    requires_certification: Mapped[bool] = mapped_column(default=False)
    icon: Mapped[str] = mapped_column(String(40), default="badge-check")
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), init=False
    )

    employee_skills: Mapped[list["EmployeeSkill"]] = relationship(
        back_populates="skill", default_factory=list, repr=False
    )


class EmployeeSkill(Base):
    """Niveau de maîtrise d'une compétence par un employé."""

    __tablename__ = "employee_skill"
    __table_args__ = (
        UniqueConstraint(
            "employee_id", "skill_id", name="uq_employee_skill_pair"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    employee_id: Mapped[int] = mapped_column(
        ForeignKey("employee.id", ondelete="CASCADE")
    )
    skill_id: Mapped[int] = mapped_column(
        ForeignKey("skill.id", ondelete="CASCADE")
    )
    level: Mapped[SkillLevel] = mapped_column(
        Enum(SkillLevel, native_enum=False, length=32),
        default=SkillLevel.INTERMEDIAIRE,
    )
    years_experience: Mapped[float] = mapped_column(Numeric(5, 2), default=0)
    certified_on: Mapped[datetime.date | None] = mapped_column(
        Date, default=None
    )
    certificate_expiry: Mapped[datetime.date | None] = mapped_column(
        Date, default=None
    )
    notes: Mapped[str] = mapped_column(Text, default="")

    employee: Mapped["Employee"] = relationship(
        back_populates="skills", default=None, repr=False
    )
    skill: Mapped["Skill"] = relationship(
        back_populates="employee_skills", default=None, repr=False
    )


class EmployeeAvailability(Base):
    """Créneau de disponibilité ou d'absence d'un employé."""

    __tablename__ = "employee_availability"

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    employee_id: Mapped[int] = mapped_column(
        ForeignKey("employee.id", ondelete="CASCADE")
    )
    type: Mapped[AvailabilityType] = mapped_column(
        Enum(AvailabilityType, native_enum=False, length=32),
        default=AvailabilityType.DISPONIBLE,
    )
    start_date: Mapped[datetime.date | None] = mapped_column(Date, default=None)
    end_date: Mapped[datetime.date | None] = mapped_column(Date, default=None)
    hours_per_day: Mapped[float] = mapped_column(Numeric(5, 2), default=7)
    is_all_day: Mapped[bool] = mapped_column(default=True)
    reason: Mapped[str] = mapped_column(String(160), default="")
    notes: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), init=False
    )

    employee: Mapped["Employee"] = relationship(
        back_populates="availabilities", default=None, repr=False
    )


class Assignment(Base):
    """Affectation d'un employé à un chantier, une parcelle ou un engin."""

    __tablename__ = "assignment"

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    employee_id: Mapped[int] = mapped_column(
        ForeignKey("employee.id", ondelete="CASCADE")
    )
    intervention_id: Mapped[int | None] = mapped_column(
        ForeignKey("intervention.id", ondelete="SET NULL"), default=None
    )
    parcel_id: Mapped[int | None] = mapped_column(
        ForeignKey("parcel.id", ondelete="SET NULL"), default=None
    )
    equipment_id: Mapped[int | None] = mapped_column(
        ForeignKey("equipment.id", ondelete="SET NULL"), default=None
    )
    maintenance_id: Mapped[int | None] = mapped_column(
        ForeignKey("maintenance_operation.id", ondelete="SET NULL"),
        default=None,
    )
    role: Mapped[AssignmentRole] = mapped_column(
        Enum(AssignmentRole, native_enum=False, length=32),
        default=AssignmentRole.OPERATEUR,
    )
    status: Mapped[AssignmentStatus] = mapped_column(
        Enum(AssignmentStatus, native_enum=False, length=32),
        default=AssignmentStatus.PROPOSEE,
    )
    title: Mapped[str] = mapped_column(String(200), default="")
    start_date: Mapped[datetime.date | None] = mapped_column(Date, default=None)
    end_date: Mapped[datetime.date | None] = mapped_column(Date, default=None)
    planned_hours: Mapped[float] = mapped_column(Numeric(6, 2), default=0)
    actual_hours: Mapped[float] = mapped_column(Numeric(6, 2), default=0)
    labor_cost: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    notes: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), init=False
    )

    employee: Mapped["Employee"] = relationship(
        back_populates="assignments", default=None, repr=False
    )
    equipment: Mapped["Equipment | None"] = relationship(
        back_populates="assignments", default=None, repr=False
    )
    maintenance: Mapped["MaintenanceOperation | None"] = relationship(
        back_populates="assignments", default=None, repr=False
    )


# ---------------------------------------------------------------------------
# Flotte d'engins et maintenance
# ---------------------------------------------------------------------------


class Equipment(Base):
    """Engin ou matériel agricole de la flotte."""

    __tablename__ = "equipment"

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    name: Mapped[str] = mapped_column(String(160))
    code: Mapped[str] = mapped_column(String(40), default="")
    category: Mapped[EquipmentCategory] = mapped_column(
        Enum(EquipmentCategory, native_enum=False, length=32),
        default=EquipmentCategory.AUTRE,
    )
    status: Mapped[EquipmentStatus] = mapped_column(
        Enum(EquipmentStatus, native_enum=False, length=32),
        default=EquipmentStatus.DISPONIBLE,
    )
    ownership: Mapped[OwnershipType] = mapped_column(
        Enum(OwnershipType, native_enum=False, length=32),
        default=OwnershipType.PROPRIETE,
    )
    brand: Mapped[str] = mapped_column(String(120), default="")
    model: Mapped[str] = mapped_column(String(120), default="")
    serial_number: Mapped[str] = mapped_column(String(120), default="")
    registration: Mapped[str] = mapped_column(String(60), default="")
    year: Mapped[int] = mapped_column(default=0)
    power_hp: Mapped[float] = mapped_column(Numeric(8, 2), default=0)
    working_width_m: Mapped[float] = mapped_column(Numeric(6, 2), default=0)
    usage_unit: Mapped[UsageUnit] = mapped_column(
        Enum(UsageUnit, native_enum=False, length=32), default=UsageUnit.HEURES
    )
    usage_counter: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    purchase_date: Mapped[datetime.date | None] = mapped_column(
        Date, default=None
    )
    purchase_price: Mapped[float] = mapped_column(Numeric(14, 2), default=0)
    residual_value: Mapped[float] = mapped_column(Numeric(14, 2), default=0)
    hourly_cost: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    fuel_consumption_l_h: Mapped[float] = mapped_column(
        Numeric(8, 2), default=0
    )
    storage_location: Mapped[str] = mapped_column(String(120), default="")
    responsible_id: Mapped[int | None] = mapped_column(
        ForeignKey("employee.id", ondelete="SET NULL"), default=None
    )
    insurance_expiry: Mapped[datetime.date | None] = mapped_column(
        Date, default=None
    )
    inspection_expiry: Mapped[datetime.date | None] = mapped_column(
        Date, default=None
    )
    next_service_date: Mapped[datetime.date | None] = mapped_column(
        Date, default=None
    )
    next_service_counter: Mapped[float] = mapped_column(
        Numeric(12, 2), default=0
    )
    service_interval_days: Mapped[int] = mapped_column(default=0)
    service_interval_counter: Mapped[float] = mapped_column(
        Numeric(12, 2), default=0
    )
    notes: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), init=False
    )

    responsible: Mapped["Employee | None"] = relationship(
        default=None, repr=False, foreign_keys=[responsible_id]
    )
    maintenances: Mapped[list["MaintenanceOperation"]] = relationship(
        back_populates="equipment", default_factory=list, repr=False
    )
    schedules: Mapped[list["MaintenanceSchedule"]] = relationship(
        back_populates="equipment", default_factory=list, repr=False
    )
    usage_logs: Mapped[list["EquipmentUsageLog"]] = relationship(
        back_populates="equipment", default_factory=list, repr=False
    )
    assignments: Mapped[list["Assignment"]] = relationship(
        back_populates="equipment", default_factory=list, repr=False
    )


class MaintenanceSchedule(Base):
    """Plan d'entretien préventif d'un engin (échéance calendaire ou compteur)."""

    __tablename__ = "maintenance_schedule"

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    equipment_id: Mapped[int] = mapped_column(
        ForeignKey("equipment.id", ondelete="CASCADE")
    )
    title: Mapped[str] = mapped_column(String(200), default="")
    kind: Mapped[MaintenanceKind] = mapped_column(
        Enum(MaintenanceKind, native_enum=False, length=32),
        default=MaintenanceKind.PREVENTIVE,
    )
    trigger_basis: Mapped[TriggerBasis] = mapped_column(
        Enum(TriggerBasis, native_enum=False, length=32),
        default=TriggerBasis.CALENDRIER,
    )
    interval_days: Mapped[int] = mapped_column(default=0)
    interval_counter: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    tolerance_days: Mapped[int] = mapped_column(default=0)
    last_done_on: Mapped[datetime.date | None] = mapped_column(
        Date, default=None
    )
    last_done_counter: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    next_due_on: Mapped[datetime.date | None] = mapped_column(
        Date, default=None
    )
    next_due_counter: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    estimated_cost: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    estimated_hours: Mapped[float] = mapped_column(Numeric(6, 2), default=0)
    responsible_id: Mapped[int | None] = mapped_column(
        ForeignKey("employee.id", ondelete="SET NULL"), default=None
    )
    is_active: Mapped[bool] = mapped_column(default=True)
    checklist: Mapped[str] = mapped_column(Text, default="")
    notes: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), init=False
    )

    equipment: Mapped["Equipment"] = relationship(
        back_populates="schedules", default=None, repr=False
    )
    responsible: Mapped["Employee | None"] = relationship(
        default=None, repr=False, foreign_keys=[responsible_id]
    )
    operations: Mapped[list["MaintenanceOperation"]] = relationship(
        back_populates="schedule", default_factory=list, repr=False
    )


class MaintenanceOperation(Base):
    """Opération de maintenance préventive ou corrective sur un engin."""

    __tablename__ = "maintenance_operation"

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    equipment_id: Mapped[int] = mapped_column(
        ForeignKey("equipment.id", ondelete="CASCADE")
    )
    schedule_id: Mapped[int | None] = mapped_column(
        ForeignKey("maintenance_schedule.id", ondelete="SET NULL"), default=None
    )
    title: Mapped[str] = mapped_column(String(200), default="")
    kind: Mapped[MaintenanceKind] = mapped_column(
        Enum(MaintenanceKind, native_enum=False, length=32),
        default=MaintenanceKind.PREVENTIVE,
    )
    status: Mapped[MaintenanceStatus] = mapped_column(
        Enum(MaintenanceStatus, native_enum=False, length=32),
        default=MaintenanceStatus.PLANIFIEE,
    )
    priority: Mapped[MaintenancePriority] = mapped_column(
        Enum(MaintenancePriority, native_enum=False, length=32),
        default=MaintenancePriority.NORMALE,
    )
    scheduled_date: Mapped[datetime.date | None] = mapped_column(
        Date, default=None
    )
    due_date: Mapped[datetime.date | None] = mapped_column(Date, default=None)
    done_date: Mapped[datetime.date | None] = mapped_column(Date, default=None)
    counter_at_service: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    downtime_hours: Mapped[float] = mapped_column(Numeric(8, 2), default=0)
    labor_hours: Mapped[float] = mapped_column(Numeric(8, 2), default=0)
    labor_cost: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    parts_cost: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    external_cost: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    total_cost: Mapped[float] = mapped_column(Numeric(14, 2), default=0)
    is_internal: Mapped[bool] = mapped_column(default=True)
    provider: Mapped[str] = mapped_column(String(160), default="")
    invoice_reference: Mapped[str] = mapped_column(String(120), default="")
    responsible_id: Mapped[int | None] = mapped_column(
        ForeignKey("employee.id", ondelete="SET NULL"), default=None
    )
    failure_description: Mapped[str] = mapped_column(Text, default="")
    work_performed: Mapped[str] = mapped_column(Text, default="")
    notes: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), init=False
    )

    equipment: Mapped["Equipment"] = relationship(
        back_populates="maintenances", default=None, repr=False
    )
    schedule: Mapped["MaintenanceSchedule | None"] = relationship(
        back_populates="operations", default=None, repr=False
    )
    responsible: Mapped["Employee | None"] = relationship(
        default=None, repr=False, foreign_keys=[responsible_id]
    )
    costs: Mapped[list["MaintenanceCost"]] = relationship(
        back_populates="maintenance", default_factory=list, repr=False
    )
    assignments: Mapped[list["Assignment"]] = relationship(
        back_populates="maintenance", default_factory=list, repr=False
    )


class MaintenanceCost(Base):
    """Ligne de coût rattachée à une opération de maintenance."""

    __tablename__ = "maintenance_cost"

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    maintenance_id: Mapped[int] = mapped_column(
        ForeignKey("maintenance_operation.id", ondelete="CASCADE")
    )
    type: Mapped[MaintenanceCostType] = mapped_column(
        Enum(MaintenanceCostType, native_enum=False, length=32),
        default=MaintenanceCostType.PIECE,
    )
    label: Mapped[str] = mapped_column(String(200), default="")
    reference: Mapped[str] = mapped_column(String(120), default="")
    supplier: Mapped[str] = mapped_column(String(160), default="")
    quantity: Mapped[float] = mapped_column(Numeric(12, 3), default=1)
    unit: Mapped[str] = mapped_column(String(20), default="u")
    unit_price: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    amount: Mapped[float] = mapped_column(Numeric(14, 2), default=0)
    incurred_on: Mapped[datetime.date | None] = mapped_column(
        Date, default=None
    )
    notes: Mapped[str] = mapped_column(Text, default="")

    maintenance: Mapped["MaintenanceOperation"] = relationship(
        back_populates="costs", default=None, repr=False
    )


class ExpenseType(Base):
    """Type de dépense personnalisable de l'exploitation."""

    __tablename__ = "expense_type"
    __table_args__ = (UniqueConstraint("name", name="uq_expense_type_name"),)

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    name: Mapped[str] = mapped_column(String(120))
    code: Mapped[str] = mapped_column(String(40), default="")
    category: Mapped[str] = mapped_column(String(80), default="")
    description: Mapped[str] = mapped_column(Text, default="")
    color_hex: Mapped[str] = mapped_column(String(9), default="#a3e635")
    icon: Mapped[str] = mapped_column(String(40), default="receipt-text")
    default_payment_method: Mapped[PaymentMethod] = mapped_column(
        Enum(PaymentMethod, native_enum=False, length=32),
        default=PaymentMethod.VIREMENT,
    )
    default_vat_rate: Mapped[float] = mapped_column(Numeric(5, 2), default=20)
    is_active: Mapped[bool] = mapped_column(default=True)
    is_archived: Mapped[bool] = mapped_column(default=False)
    notes: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), init=False
    )

    expenses: Mapped[list["Expense"]] = relationship(
        back_populates="expense_type", default_factory=list, repr=False
    )


class Expense(Base):
    """Dépense libre, rattachable à n'importe quel actif de l'exploitation."""

    __tablename__ = "expense"

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    expense_type_id: Mapped[int] = mapped_column(
        ForeignKey("expense_type.id", ondelete="RESTRICT")
    )
    label: Mapped[str] = mapped_column(String(200))
    reference: Mapped[str] = mapped_column(String(120), default="")
    supplier: Mapped[str] = mapped_column(String(160), default="")
    invoice_reference: Mapped[str] = mapped_column(String(120), default="")
    status: Mapped[ExpenseStatus] = mapped_column(
        Enum(ExpenseStatus, native_enum=False, length=32),
        default=ExpenseStatus.ENGAGEE,
    )
    payment_method: Mapped[PaymentMethod] = mapped_column(
        Enum(PaymentMethod, native_enum=False, length=32),
        default=PaymentMethod.VIREMENT,
    )
    quantity: Mapped[float] = mapped_column(Numeric(12, 3), default=1)
    unit: Mapped[str] = mapped_column(String(20), default="u")
    amount_ht: Mapped[float] = mapped_column(Numeric(14, 2), default=0)
    vat_rate: Mapped[float] = mapped_column(Numeric(5, 2), default=20)
    amount_ttc: Mapped[float] = mapped_column(Numeric(14, 2), default=0)
    incurred_on: Mapped[datetime.date | None] = mapped_column(
        Date, default=None
    )
    due_date: Mapped[datetime.date | None] = mapped_column(Date, default=None)
    paid_on: Mapped[datetime.date | None] = mapped_column(Date, default=None)
    parcel_id: Mapped[int | None] = mapped_column(
        ForeignKey("parcel.id", ondelete="SET NULL"), default=None
    )
    crop_id: Mapped[int | None] = mapped_column(
        ForeignKey("crop.id", ondelete="SET NULL"), default=None
    )
    employee_id: Mapped[int | None] = mapped_column(
        ForeignKey("employee.id", ondelete="SET NULL"), default=None
    )
    equipment_id: Mapped[int | None] = mapped_column(
        ForeignKey("equipment.id", ondelete="SET NULL"), default=None
    )
    intervention_id: Mapped[int | None] = mapped_column(
        ForeignKey("intervention.id", ondelete="SET NULL"), default=None
    )
    maintenance_id: Mapped[int | None] = mapped_column(
        ForeignKey("maintenance_operation.id", ondelete="SET NULL"),
        default=None,
    )
    is_archived: Mapped[bool] = mapped_column(default=False)
    notes: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), init=False
    )

    expense_type: Mapped["ExpenseType"] = relationship(
        back_populates="expenses", default=None, repr=False
    )


# ---------------------------------------------------------------------------
# Guide Agricole : base de connaissances éditoriale versionnée
# ---------------------------------------------------------------------------


class GuideStatus(str, enum.Enum):
    """Cycle de vie éditorial d'un contenu du guide."""

    BROUILLON = "brouillon"
    RELECTURE = "relecture"
    PUBLIE = "publie"
    ARCHIVE = "archive"


class GuideAudience(str, enum.Enum):
    """Niveau de lecture visé (double lecture agricole / AgriPro)."""

    AGRICOLE = "agricole"
    AGRIPRO = "agripro"
    MIXTE = "mixte"


class GuideDifficulty(str, enum.Enum):
    DECOUVERTE = "decouverte"
    INTERMEDIAIRE = "intermediaire"
    AVANCE = "avance"


class GuideRuleKind(str, enum.Enum):
    """Nature d'une règle éditoriale attachée à un module ou un champ."""

    POURQUOI = "pourquoi"
    ATTENTION = "attention"
    COHERENCE = "coherence"
    BONNE_PRATIQUE = "bonne_pratique"


class GuideSeverity(str, enum.Enum):
    INFO = "info"
    ATTENTION = "attention"
    CRITIQUE = "critique"


class GuideChangeKind(str, enum.Enum):
    AJOUT = "ajout"
    MISE_A_JOUR = "mise_a_jour"
    CORRECTION = "correction"
    SUPPRESSION = "suppression"


class GuideModule(Base):
    """Module applicatif cible d'un contenu du guide (lien direct)."""

    __tablename__ = "guide_module"
    __table_args__ = (UniqueConstraint("key", name="uq_guide_module_key"),)

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    key: Mapped[str] = mapped_column(String(60))
    label: Mapped[str] = mapped_column(String(160))
    route: Mapped[str] = mapped_column(String(160), default="/")
    icon: Mapped[str] = mapped_column(String(40), default="book-open")
    description: Mapped[str] = mapped_column(Text, default="")
    position: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), init=False
    )


class GuideCategory(Base):
    """Catégorie thématique du guide (fondamentaux, parcelles, cultures...)."""

    __tablename__ = "guide_category"
    __table_args__ = (UniqueConstraint("key", name="uq_guide_category_key"),)

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    key: Mapped[str] = mapped_column(String(60))
    name: Mapped[str] = mapped_column(String(160))
    tagline: Mapped[str] = mapped_column(String(220), default="")
    description: Mapped[str] = mapped_column(Text, default="")
    icon: Mapped[str] = mapped_column(String(40), default="book-open")
    color_hex: Mapped[str] = mapped_column(String(9), default="#a3e635")
    accent_hex: Mapped[str] = mapped_column(String(9), default="#fbbf24")
    module_route: Mapped[str] = mapped_column(String(160), default="/")
    position: Mapped[int] = mapped_column(default=0)
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), init=False
    )

    articles: Mapped[list["GuideArticle"]] = relationship(
        back_populates="category", default_factory=list, repr=False
    )


class GuideArticle(Base):
    """Article du guide avec double lecture agricole et AgriPro."""

    __tablename__ = "guide_article"
    __table_args__ = (UniqueConstraint("slug", name="uq_guide_article_slug"),)

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    category_id: Mapped[int] = mapped_column(
        ForeignKey("guide_category.id", ondelete="CASCADE")
    )
    slug: Mapped[str] = mapped_column(String(120))
    title: Mapped[str] = mapped_column(String(220))
    subtitle: Mapped[str] = mapped_column(String(260), default="")
    summary: Mapped[str] = mapped_column(Text, default="")
    # Lecture « agricole » : vocabulaire de terrain, phrases courtes.
    body_farmer: Mapped[str] = mapped_column(Text, default="")
    # Lecture « AgriPro » : vocabulaire technique, indicateurs, normes.
    body_pro: Mapped[str] = mapped_column(Text, default="")
    audience: Mapped[GuideAudience] = mapped_column(
        Enum(GuideAudience, native_enum=False, length=32),
        default=GuideAudience.MIXTE,
    )
    status: Mapped[GuideStatus] = mapped_column(
        Enum(GuideStatus, native_enum=False, length=32),
        default=GuideStatus.PUBLIE,
    )
    difficulty: Mapped[GuideDifficulty] = mapped_column(
        Enum(GuideDifficulty, native_enum=False, length=32),
        default=GuideDifficulty.DECOUVERTE,
    )
    reading_minutes: Mapped[int] = mapped_column(default=3)
    keywords: Mapped[str] = mapped_column(Text, default="")
    tags: Mapped[str] = mapped_column(Text, default="")
    author: Mapped[str] = mapped_column(String(120), default="")
    version_label: Mapped[str] = mapped_column(String(40), default="1.0.0")
    module_route: Mapped[str] = mapped_column(String(160), default="")
    published_on: Mapped[datetime.date | None] = mapped_column(
        Date, default=None
    )
    reviewed_on: Mapped[datetime.date | None] = mapped_column(
        Date, default=None
    )
    is_featured: Mapped[bool] = mapped_column(default=False)
    position: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), init=False
    )

    category: Mapped["GuideCategory"] = relationship(
        back_populates="articles", default=None, repr=False
    )
    links: Mapped[list["GuideArticleLink"]] = relationship(
        back_populates="article", default_factory=list, repr=False
    )


class GuideArticleLink(Base):
    """Lien direct d'un article vers un écran ou un module de l'application."""

    __tablename__ = "guide_article_link"

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    article_id: Mapped[int] = mapped_column(
        ForeignKey("guide_article.id", ondelete="CASCADE")
    )
    module_id: Mapped[int | None] = mapped_column(
        ForeignKey("guide_module.id", ondelete="SET NULL"), default=None
    )
    label: Mapped[str] = mapped_column(String(160), default="")
    route: Mapped[str] = mapped_column(String(160), default="/")
    icon: Mapped[str] = mapped_column(String(40), default="arrow-right")
    description: Mapped[str] = mapped_column(Text, default="")
    position: Mapped[int] = mapped_column(default=0)

    article: Mapped["GuideArticle"] = relationship(
        back_populates="links", init=False, repr=False
    )


class GuideProcedure(Base):
    """Procédure interactive pas à pas rattachée à un module."""

    __tablename__ = "guide_procedure"
    __table_args__ = (UniqueConstraint("slug", name="uq_guide_procedure_slug"),)

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    category_id: Mapped[int] = mapped_column(
        ForeignKey("guide_category.id", ondelete="CASCADE")
    )
    article_id: Mapped[int | None] = mapped_column(
        ForeignKey("guide_article.id", ondelete="SET NULL"), default=None
    )
    slug: Mapped[str] = mapped_column(String(120), default="")
    title: Mapped[str] = mapped_column(String(220), default="")
    objective: Mapped[str] = mapped_column(Text, default="")
    context: Mapped[str] = mapped_column(Text, default="")
    expected_result: Mapped[str] = mapped_column(Text, default="")
    prerequisites: Mapped[str] = mapped_column(Text, default="")
    module_route: Mapped[str] = mapped_column(String(160), default="/")
    estimated_minutes: Mapped[int] = mapped_column(default=5)
    difficulty: Mapped[GuideDifficulty] = mapped_column(
        Enum(GuideDifficulty, native_enum=False, length=32),
        default=GuideDifficulty.DECOUVERTE,
    )
    audience: Mapped[GuideAudience] = mapped_column(
        Enum(GuideAudience, native_enum=False, length=32),
        default=GuideAudience.MIXTE,
    )
    status: Mapped[GuideStatus] = mapped_column(
        Enum(GuideStatus, native_enum=False, length=32),
        default=GuideStatus.PUBLIE,
    )
    version_label: Mapped[str] = mapped_column(String(40), default="1.0.0")
    position: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), init=False
    )

    steps: Mapped[list["GuideProcedureStep"]] = relationship(
        back_populates="procedure", default_factory=list, repr=False
    )


class GuideProcedureStep(Base):
    """Étape d'une procédure, en double lecture, avec garde-fous."""

    __tablename__ = "guide_procedure_step"

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    procedure_id: Mapped[int] = mapped_column(
        ForeignKey("guide_procedure.id", ondelete="CASCADE")
    )
    position: Mapped[int] = mapped_column(default=0)
    title: Mapped[str] = mapped_column(String(220), default="")
    instruction_farmer: Mapped[str] = mapped_column(Text, default="")
    instruction_pro: Mapped[str] = mapped_column(Text, default="")
    ui_hint: Mapped[str] = mapped_column(Text, default="")
    module_route: Mapped[str] = mapped_column(String(160), default="")
    field_reference: Mapped[str] = mapped_column(String(160), default="")
    why: Mapped[str] = mapped_column(Text, default="")
    warning: Mapped[str] = mapped_column(Text, default="")
    duration_minutes: Mapped[int] = mapped_column(default=1)
    is_optional: Mapped[bool] = mapped_column(default=False)

    procedure: Mapped["GuideProcedure"] = relationship(
        back_populates="steps", default=None, repr=False
    )


class GuideTerm(Base):
    """Entrée du dictionnaire agricole, en double lecture."""

    __tablename__ = "guide_term"
    __table_args__ = (UniqueConstraint("slug", name="uq_guide_term_slug"),)

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    category_id: Mapped[int | None] = mapped_column(
        ForeignKey("guide_category.id", ondelete="SET NULL"), default=None
    )
    slug: Mapped[str] = mapped_column(String(120), default="")
    term: Mapped[str] = mapped_column(String(160), default="")
    acronym: Mapped[str] = mapped_column(String(40), default="")
    definition_farmer: Mapped[str] = mapped_column(Text, default="")
    definition_pro: Mapped[str] = mapped_column(Text, default="")
    unit: Mapped[str] = mapped_column(String(40), default="")
    formula: Mapped[str] = mapped_column(String(220), default="")
    example: Mapped[str] = mapped_column(Text, default="")
    synonyms: Mapped[str] = mapped_column(Text, default="")
    related_terms: Mapped[str] = mapped_column(Text, default="")
    module_route: Mapped[str] = mapped_column(String(160), default="")
    status: Mapped[GuideStatus] = mapped_column(
        Enum(GuideStatus, native_enum=False, length=32),
        default=GuideStatus.PUBLIE,
    )
    version_label: Mapped[str] = mapped_column(String(40), default="1.0.0")
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), init=False
    )


class GuideFaq(Base):
    """Question fréquente, avec réponse en double lecture."""

    __tablename__ = "guide_faq"

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    category_id: Mapped[int] = mapped_column(
        ForeignKey("guide_category.id", ondelete="CASCADE")
    )
    article_id: Mapped[int | None] = mapped_column(
        ForeignKey("guide_article.id", ondelete="SET NULL"), default=None
    )
    question: Mapped[str] = mapped_column(String(300), default="")
    answer_farmer: Mapped[str] = mapped_column(Text, default="")
    answer_pro: Mapped[str] = mapped_column(Text, default="")
    audience: Mapped[GuideAudience] = mapped_column(
        Enum(GuideAudience, native_enum=False, length=32),
        default=GuideAudience.MIXTE,
    )
    status: Mapped[GuideStatus] = mapped_column(
        Enum(GuideStatus, native_enum=False, length=32),
        default=GuideStatus.PUBLIE,
    )
    keywords: Mapped[str] = mapped_column(Text, default="")
    module_route: Mapped[str] = mapped_column(String(160), default="")
    is_frequent: Mapped[bool] = mapped_column(default=False)
    position: Mapped[int] = mapped_column(default=0)
    version_label: Mapped[str] = mapped_column(String(40), default="1.0.0")
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), init=False
    )


class GuideRule(Base):
    """Règle de cohérence, explication « Pourquoi ? » ou avertissement."""

    __tablename__ = "guide_rule"
    __table_args__ = (UniqueConstraint("code", name="uq_guide_rule_code"),)

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    category_id: Mapped[int | None] = mapped_column(
        ForeignKey("guide_category.id", ondelete="SET NULL"), default=None
    )
    article_id: Mapped[int | None] = mapped_column(
        ForeignKey("guide_article.id", ondelete="SET NULL"), default=None
    )
    code: Mapped[str] = mapped_column(String(60), default="")
    kind: Mapped[GuideRuleKind] = mapped_column(
        Enum(GuideRuleKind, native_enum=False, length=32),
        default=GuideRuleKind.COHERENCE,
    )
    severity: Mapped[GuideSeverity] = mapped_column(
        Enum(GuideSeverity, native_enum=False, length=32),
        default=GuideSeverity.INFO,
    )
    title: Mapped[str] = mapped_column(String(240), default="")
    statement: Mapped[str] = mapped_column(Text, default="")
    rationale: Mapped[str] = mapped_column(Text, default="")
    consequence: Mapped[str] = mapped_column(Text, default="")
    remediation: Mapped[str] = mapped_column(Text, default="")
    module_route: Mapped[str] = mapped_column(String(160), default="")
    field_reference: Mapped[str] = mapped_column(String(160), default="")
    is_blocking: Mapped[bool] = mapped_column(default=False)
    status: Mapped[GuideStatus] = mapped_column(
        Enum(GuideStatus, native_enum=False, length=32),
        default=GuideStatus.PUBLIE,
    )
    version_label: Mapped[str] = mapped_column(String(40), default="1.0.0")
    position: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), init=False
    )


class GuideLearningPath(Base):
    """Parcours d'apprentissage progressif du guide."""

    __tablename__ = "guide_learning_path"
    __table_args__ = (UniqueConstraint("slug", name="uq_guide_path_slug"),)

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    slug: Mapped[str] = mapped_column(String(120), default="")
    title: Mapped[str] = mapped_column(String(220), default="")
    subtitle: Mapped[str] = mapped_column(String(260), default="")
    objective: Mapped[str] = mapped_column(Text, default="")
    audience: Mapped[GuideAudience] = mapped_column(
        Enum(GuideAudience, native_enum=False, length=32),
        default=GuideAudience.AGRICOLE,
    )
    difficulty: Mapped[GuideDifficulty] = mapped_column(
        Enum(GuideDifficulty, native_enum=False, length=32),
        default=GuideDifficulty.DECOUVERTE,
    )
    status: Mapped[GuideStatus] = mapped_column(
        Enum(GuideStatus, native_enum=False, length=32),
        default=GuideStatus.PUBLIE,
    )
    estimated_minutes: Mapped[int] = mapped_column(default=30)
    icon: Mapped[str] = mapped_column(String(40), default="graduation-cap")
    color_hex: Mapped[str] = mapped_column(String(9), default="#a3e635")
    version_label: Mapped[str] = mapped_column(String(40), default="1.0.0")
    position: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), init=False
    )

    steps: Mapped[list["GuideLearningStep"]] = relationship(
        back_populates="path", default_factory=list, repr=False
    )


class GuideLearningStep(Base):
    """Étape d'un parcours d'apprentissage (article, procédure ou module)."""

    __tablename__ = "guide_learning_step"

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    path_id: Mapped[int] = mapped_column(
        ForeignKey("guide_learning_path.id", ondelete="CASCADE")
    )
    category_id: Mapped[int | None] = mapped_column(
        ForeignKey("guide_category.id", ondelete="SET NULL"), default=None
    )
    article_id: Mapped[int | None] = mapped_column(
        ForeignKey("guide_article.id", ondelete="SET NULL"), default=None
    )
    procedure_id: Mapped[int | None] = mapped_column(
        ForeignKey("guide_procedure.id", ondelete="SET NULL"), default=None
    )
    position: Mapped[int] = mapped_column(default=0)
    title: Mapped[str] = mapped_column(String(220), default="")
    description: Mapped[str] = mapped_column(Text, default="")
    milestone: Mapped[str] = mapped_column(String(220), default="")
    module_route: Mapped[str] = mapped_column(String(160), default="")
    duration_minutes: Mapped[int] = mapped_column(default=5)
    is_optional: Mapped[bool] = mapped_column(default=False)

    path: Mapped["GuideLearningPath"] = relationship(
        back_populates="steps", default=None, repr=False
    )


class GuideVersion(Base):
    """Version publiée du guide (versionnage éditorial consultable)."""

    __tablename__ = "guide_version"
    __table_args__ = (
        UniqueConstraint("version_label", name="uq_guide_version_label"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    version_label: Mapped[str] = mapped_column(String(40), default="1.0.0")
    title: Mapped[str] = mapped_column(String(220), default="")
    summary: Mapped[str] = mapped_column(Text, default="")
    changelog: Mapped[str] = mapped_column(Text, default="")
    author: Mapped[str] = mapped_column(String(120), default="")
    status: Mapped[GuideStatus] = mapped_column(
        Enum(GuideStatus, native_enum=False, length=32),
        default=GuideStatus.PUBLIE,
    )
    published_on: Mapped[datetime.date | None] = mapped_column(
        Date, default=None
    )
    is_current: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), init=False
    )

    entries: Mapped[list["GuideVersionEntry"]] = relationship(
        back_populates="version", default_factory=list, repr=False
    )


class GuideVersionEntry(Base):
    """Ligne de changelog rattachée à une version du guide."""

    __tablename__ = "guide_version_entry"

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    version_id: Mapped[int] = mapped_column(
        ForeignKey("guide_version.id", ondelete="CASCADE")
    )
    entity_type: Mapped[str] = mapped_column(String(60), default="ARTICLE")
    entity_ref: Mapped[str] = mapped_column(String(160), default="")
    change_kind: Mapped[GuideChangeKind] = mapped_column(
        Enum(GuideChangeKind, native_enum=False, length=32),
        default=GuideChangeKind.AJOUT,
    )
    summary: Mapped[str] = mapped_column(Text, default="")
    author: Mapped[str] = mapped_column(String(120), default="")
    position: Mapped[int] = mapped_column(default=0)

    version: Mapped["GuideVersion"] = relationship(
        back_populates="entries", default=None, repr=False
    )


class RemediationLog(Base):
    """Trace minimale d'une décision de remédiation d'un état d'exploitation.

    Table locale créée par l'initialisation SQLite existante : aucune migration
    n'est nécessaire. Elle documente ce qui a été décidé (alerte traitée, stock
    commandé ou reporté, contour vérifié ou à relever), par qui et pourquoi.
    """

    __tablename__ = "remediation_log"

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    domain: Mapped[str] = mapped_column(String(32), default="ALERTE")
    target_kind: Mapped[str] = mapped_column(String(40), default="")
    target_id: Mapped[int] = mapped_column(default=0)
    target_label: Mapped[str] = mapped_column(String(200), default="")
    action: Mapped[str] = mapped_column(String(40), default="")
    note: Mapped[str] = mapped_column(Text, default="")
    author: Mapped[str] = mapped_column(
        String(120), default="Responsable d'exploitation"
    )
    module_route: Mapped[str] = mapped_column(String(160), default="/")
    decided_on: Mapped[datetime.date | None] = mapped_column(Date, default=None)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), init=False
    )


# ---------------------------------------------------------------------------
# Référentiel structuré Catégorie → Culture → Espèce → Variété
# ---------------------------------------------------------------------------


class CultureCycle(str, enum.Enum):
    """Durée de cycle d'une culture du référentiel."""

    ANNUELLE = "annuelle"
    BISANNUELLE = "bisannuelle"
    PERENNE = "perenne"


class WaterNeed(str, enum.Enum):
    """Besoin en eau global d'une culture ou d'une espèce."""

    FAIBLE = "faible"
    MODEREE = "moderee"
    ELEVEE = "elevee"
    TRES_ELEVEE = "tres_elevee"


class ToleranceLevel(str, enum.Enum):
    """Niveau de tolérance (sécheresse, salinité, froid)."""

    FAIBLE = "faible"
    MOYENNE = "moyenne"
    BONNE = "bonne"
    EXCELLENTE = "excellente"


class CropCategory(Base):
    """Catégorie racine du référentiel (céréales, dattes, maraîchage...)."""

    __tablename__ = "crop_category"
    __table_args__ = (UniqueConstraint("key", name="uq_crop_category_key"),)

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    key: Mapped[str] = mapped_column(String(60))
    name: Mapped[str] = mapped_column(String(160))
    tagline: Mapped[str] = mapped_column(String(240), default="")
    description: Mapped[str] = mapped_column(Text, default="")
    icon: Mapped[str] = mapped_column(String(40), default="sprout")
    color_hex: Mapped[str] = mapped_column(String(9), default="#a3e635")
    accent_hex: Mapped[str] = mapped_column(String(9), default="#fbbf24")
    position: Mapped[int] = mapped_column(default=0)
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), init=False
    )

    cultures: Mapped[list["CropCulture"]] = relationship(
        back_populates="category", default_factory=list, repr=False
    )


class CropCulture(Base):
    """Culture d'une catégorie (blé, palmier dattier, tomate...)."""

    __tablename__ = "crop_culture"
    __table_args__ = (UniqueConstraint("key", name="uq_crop_culture_key"),)

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    category_id: Mapped[int] = mapped_column(
        ForeignKey("crop_category.id", ondelete="CASCADE")
    )
    key: Mapped[str] = mapped_column(String(80))
    name: Mapped[str] = mapped_column(String(160))
    common_name: Mapped[str] = mapped_column(String(160), default="")
    botanical_family: Mapped[str] = mapped_column(String(120), default="")
    cycle: Mapped[CultureCycle] = mapped_column(
        Enum(CultureCycle, native_enum=False, length=32),
        default=CultureCycle.ANNUELLE,
    )
    water_need: Mapped[WaterNeed] = mapped_column(
        Enum(WaterNeed, native_enum=False, length=32),
        default=WaterNeed.MODEREE,
    )
    icon: Mapped[str] = mapped_column(String(40), default="sprout")
    color_hex: Mapped[str] = mapped_column(String(9), default="#4ade80")
    usage: Mapped[str] = mapped_column(String(240), default="")
    description: Mapped[str] = mapped_column(Text, default="")
    position: Mapped[int] = mapped_column(default=0)
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), init=False
    )

    category: Mapped["CropCategory"] = relationship(
        back_populates="cultures", default=None, repr=False
    )
    species: Mapped[list["CropSpecies"]] = relationship(
        back_populates="culture", default_factory=list, repr=False
    )


class CropSpecies(Base):
    """Espèce botanique d'une culture, porteuse des constantes agronomiques."""

    __tablename__ = "crop_species"
    __table_args__ = (UniqueConstraint("key", name="uq_crop_species_key"),)

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    culture_id: Mapped[int] = mapped_column(
        ForeignKey("crop_culture.id", ondelete="CASCADE")
    )
    key: Mapped[str] = mapped_column(String(100))
    name: Mapped[str] = mapped_column(String(180))
    scientific_name: Mapped[str] = mapped_column(String(180), default="")
    botanical_family: Mapped[str] = mapped_column(String(120), default="")
    cycle_days_min: Mapped[int] = mapped_column(default=0)
    cycle_days_max: Mapped[int] = mapped_column(default=0)
    sowing_window: Mapped[str] = mapped_column(String(120), default="")
    harvest_window: Mapped[str] = mapped_column(String(120), default="")
    water_requirement_mm: Mapped[float] = mapped_column(
        Numeric(8, 1), default=0
    )
    rooting_depth_cm: Mapped[float] = mapped_column(Numeric(6, 1), default=0)
    base_temperature_c: Mapped[float] = mapped_column(Numeric(5, 2), default=0)
    optimal_ph_min: Mapped[float] = mapped_column(Numeric(4, 2), default=6)
    optimal_ph_max: Mapped[float] = mapped_column(Numeric(4, 2), default=8)
    salinity_tolerance: Mapped[ToleranceLevel] = mapped_column(
        Enum(ToleranceLevel, native_enum=False, length=32),
        default=ToleranceLevel.MOYENNE,
    )
    nitrogen_need_kg_ha: Mapped[float] = mapped_column(Numeric(8, 1), default=0)
    phosphorus_need_kg_ha: Mapped[float] = mapped_column(
        Numeric(8, 1), default=0
    )
    potassium_need_kg_ha: Mapped[float] = mapped_column(
        Numeric(8, 1), default=0
    )
    default_density: Mapped[str] = mapped_column(String(160), default="")
    main_pests: Mapped[str] = mapped_column(Text, default="")
    main_diseases: Mapped[str] = mapped_column(Text, default="")
    notes: Mapped[str] = mapped_column(Text, default="")
    position: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), init=False
    )

    culture: Mapped["CropCulture"] = relationship(
        back_populates="species", default=None, repr=False
    )
    varieties: Mapped[list["CropCatalogVariety"]] = relationship(
        back_populates="species", default_factory=list, repr=False
    )


class CropCatalogVariety(Base):
    """Variété du référentiel, éventuellement reliée à `crop_variety`."""

    __tablename__ = "crop_catalog_variety"
    __table_args__ = (
        UniqueConstraint("key", name="uq_crop_catalog_variety_key"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    species_id: Mapped[int] = mapped_column(
        ForeignKey("crop_species.id", ondelete="CASCADE")
    )
    # Correspondance avec le référentiel variétal historique de l'exploitation.
    crop_variety_id: Mapped[int | None] = mapped_column(
        ForeignKey("crop_variety.id", ondelete="SET NULL"), default=None
    )
    key: Mapped[str] = mapped_column(String(140))
    name: Mapped[str] = mapped_column(String(160))
    local_name: Mapped[str] = mapped_column(String(160), default="")
    maturity_group: Mapped[str] = mapped_column(String(80), default="")
    cycle_days: Mapped[int] = mapped_column(default=0)
    expected_yield_t_ha: Mapped[float] = mapped_column(
        Numeric(10, 2), default=0
    )
    quality_grade: Mapped[str] = mapped_column(String(160), default="")
    color_hex: Mapped[str] = mapped_column(String(9), default="#a3e635")
    sowing_window: Mapped[str] = mapped_column(String(120), default="")
    harvest_window: Mapped[str] = mapped_column(String(120), default="")
    drought_tolerance: Mapped[ToleranceLevel] = mapped_column(
        Enum(ToleranceLevel, native_enum=False, length=32),
        default=ToleranceLevel.MOYENNE,
    )
    is_reference: Mapped[bool] = mapped_column(default=False)
    notes: Mapped[str] = mapped_column(Text, default="")
    position: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), init=False
    )

    species: Mapped["CropSpecies"] = relationship(
        back_populates="varieties", default=None, repr=False
    )


# ---------------------------------------------------------------------------
# Suivi phénologique multicultures
# ---------------------------------------------------------------------------


class PhenologySystem(str, enum.Enum):
    """Système de notation des stades utilisé par un profil."""

    BBCH = "bbch"
    LOCAL = "local"
    MIXTE = "mixte"


class StageObservationStatus(str, enum.Enum):
    """Cycle de vie d'une observation de stade."""

    PROPOSE = "propose"
    CONFIRME = "confirme"
    CORRIGE = "corrige"
    REJETE = "rejete"


class StageObservationSource(str, enum.Enum):
    """Origine de l'information de stade."""

    HUMAINE = "humaine"
    SYSTEME = "systeme"
    IMPORT = "import"


class StageRecommendationDomain(str, enum.Enum):
    """Domaine métier concerné par une recommandation de stade."""

    IRRIGATION = "irrigation"
    FERTILISATION = "fertilisation"
    TRAITEMENT = "traitement"
    SURVEILLANCE = "surveillance"
    TRAVAIL_DU_SOL = "travail_du_sol"
    RECOLTE = "recolte"
    AUTRE = "autre"


class StageRecommendationConfidence(str, enum.Enum):
    """Niveau de confiance : rien n'est prescriptif par défaut."""

    INDICATIVE = "indicative"
    VALIDEE = "validee"
    REGLEMENTAIRE = "reglementaire"


class StageMediaKind(str, enum.Enum):
    PHOTO = "photo"
    DOCUMENT = "document"
    AUTRE = "autre"


class CropPhenologyProfile(Base):
    """Cycle phénologique propre à une culture, une espèce ou une variété.

    Il n'existe volontairement aucune liste globale de stades : chaque profil
    porte son propre enchaînement, rattaché au référentiel structuré existant
    (`crop_culture`, `crop_species`, `crop_catalog_variety`).
    """

    __tablename__ = "crop_phenology_profile"
    __table_args__ = (UniqueConstraint("key", name="uq_phenology_profile_key"),)

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    culture_id: Mapped[int] = mapped_column(
        ForeignKey("crop_culture.id", ondelete="CASCADE")
    )
    # Spécialisations facultatives : espèce puis variété du référentiel.
    species_id: Mapped[int | None] = mapped_column(
        ForeignKey("crop_species.id", ondelete="SET NULL"), default=None
    )
    catalog_variety_id: Mapped[int | None] = mapped_column(
        ForeignKey("crop_catalog_variety.id", ondelete="SET NULL"),
        default=None,
    )
    key: Mapped[str] = mapped_column(String(120), default="")
    name: Mapped[str] = mapped_column(String(180), default="")
    phenological_system: Mapped[PhenologySystem] = mapped_column(
        Enum(PhenologySystem, native_enum=False, length=32),
        default=PhenologySystem.LOCAL,
    )
    summary: Mapped[str] = mapped_column(Text, default="")
    source: Mapped[str] = mapped_column(String(200), default="")
    is_default: Mapped[bool] = mapped_column(default=False)
    is_active: Mapped[bool] = mapped_column(default=True)
    position: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), init=False
    )

    stages: Mapped[list["CropPhenologyStage"]] = relationship(
        back_populates="profile", default_factory=list, repr=False
    )


class CropPhenologyStage(Base):
    """Stade ordonné d'un profil phénologique."""

    __tablename__ = "crop_phenology_stage"
    __table_args__ = (
        UniqueConstraint(
            "profile_id", "key", name="uq_phenology_stage_profile_key"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    profile_id: Mapped[int] = mapped_column(
        ForeignKey("crop_phenology_profile.id", ondelete="CASCADE")
    )
    key: Mapped[str] = mapped_column(String(120), default="")
    name: Mapped[str] = mapped_column(String(180), default="")
    position: Mapped[int] = mapped_column(default=0)
    bbch_code: Mapped[str] = mapped_column(String(40), default="")
    phenological_system: Mapped[PhenologySystem] = mapped_column(
        Enum(PhenologySystem, native_enum=False, length=32),
        default=PhenologySystem.LOCAL,
    )
    description: Mapped[str] = mapped_column(Text, default="")
    recognition: Mapped[str] = mapped_column(Text, default="")
    watchpoints: Mapped[str] = mapped_column(Text, default="")
    common_errors: Mapped[str] = mapped_column(Text, default="")
    duration_days_min: Mapped[int] = mapped_column(default=0)
    duration_days_max: Mapped[int] = mapped_column(default=0)
    is_critical: Mapped[bool] = mapped_column(default=False)
    is_active: Mapped[bool] = mapped_column(default=True)
    icon: Mapped[str] = mapped_column(String(40), default="sprout")
    color_hex: Mapped[str] = mapped_column(String(9), default="#a3e635")
    guide_article_slug: Mapped[str] = mapped_column(String(120), default="")
    guide_term_slug: Mapped[str] = mapped_column(String(120), default="")
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), init=False
    )

    profile: Mapped["CropPhenologyProfile"] = relationship(
        back_populates="stages", default=None, repr=False
    )
    recommendations: Mapped[list["CropStageRecommendation"]] = relationship(
        back_populates="stage", default_factory=list, repr=False
    )


class CropStageObservation(Base):
    """Observation datée du stade réel d'une culture sur une parcelle."""

    __tablename__ = "crop_stage_observation"

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    crop_id: Mapped[int] = mapped_column(
        ForeignKey("crop.id", ondelete="CASCADE")
    )
    parcel_id: Mapped[int | None] = mapped_column(
        ForeignKey("parcel.id", ondelete="SET NULL"), default=None
    )
    profile_id: Mapped[int | None] = mapped_column(
        ForeignKey("crop_phenology_profile.id", ondelete="SET NULL"),
        default=None,
    )
    stage_id: Mapped[int | None] = mapped_column(
        ForeignKey("crop_phenology_stage.id", ondelete="SET NULL"), default=None
    )
    season: Mapped[str] = mapped_column(String(40), default="")
    observed_on: Mapped[datetime.date | None] = mapped_column(
        Date, default=None
    )
    observed_at_time: Mapped[str] = mapped_column(String(10), default="")
    observer: Mapped[str] = mapped_column(String(120), default="")
    status: Mapped[StageObservationStatus] = mapped_column(
        Enum(StageObservationStatus, native_enum=False, length=32),
        default=StageObservationStatus.CONFIRME,
    )
    source: Mapped[StageObservationSource] = mapped_column(
        Enum(StageObservationSource, native_enum=False, length=32),
        default=StageObservationSource.HUMAINE,
    )
    vigour: Mapped[str] = mapped_column(String(80), default="")
    homogeneity: Mapped[str] = mapped_column(String(80), default="")
    anomalies: Mapped[str] = mapped_column(Text, default="")
    diseases_observed: Mapped[str] = mapped_column(Text, default="")
    pests_observed: Mapped[str] = mapped_column(Text, default="")
    water_stress: Mapped[bool] = mapped_column(default=False)
    thermal_stress: Mapped[bool] = mapped_column(default=False)
    comment: Mapped[str] = mapped_column(Text, default="")
    progress_percent: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), init=False
    )

    media: Mapped[list["CropStageMedia"]] = relationship(
        back_populates="observation", default_factory=list, repr=False
    )


class CropStageChange(Base):
    """Historique des changements de stade : jamais purgé automatiquement."""

    __tablename__ = "crop_stage_change"

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    crop_id: Mapped[int] = mapped_column(
        ForeignKey("crop.id", ondelete="CASCADE")
    )
    observation_id: Mapped[int | None] = mapped_column(
        ForeignKey("crop_stage_observation.id", ondelete="SET NULL"),
        default=None,
    )
    previous_stage_id: Mapped[int | None] = mapped_column(
        ForeignKey("crop_phenology_stage.id", ondelete="SET NULL"), default=None
    )
    new_stage_id: Mapped[int | None] = mapped_column(
        ForeignKey("crop_phenology_stage.id", ondelete="SET NULL"), default=None
    )
    changed_on: Mapped[datetime.date | None] = mapped_column(Date, default=None)
    author: Mapped[str] = mapped_column(String(120), default="")
    comment: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), init=False
    )


class CropStageRecommendation(Base):
    """Opération généralement associée à un stade, jamais prescriptive."""

    __tablename__ = "crop_stage_recommendation"

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    stage_id: Mapped[int] = mapped_column(
        ForeignKey("crop_phenology_stage.id", ondelete="CASCADE")
    )
    domain: Mapped[StageRecommendationDomain] = mapped_column(
        Enum(StageRecommendationDomain, native_enum=False, length=32),
        default=StageRecommendationDomain.SURVEILLANCE,
    )
    title: Mapped[str] = mapped_column(String(220), default="")
    statement: Mapped[str] = mapped_column(Text, default="")
    confidence: Mapped[StageRecommendationConfidence] = mapped_column(
        Enum(StageRecommendationConfidence, native_enum=False, length=32),
        default=StageRecommendationConfidence.INDICATIVE,
    )
    source: Mapped[str] = mapped_column(String(220), default="")
    # Une recommandation ne se transforme jamais seule en intervention.
    is_advisory: Mapped[bool] = mapped_column(default=True)
    guide_article_slug: Mapped[str] = mapped_column(String(120), default="")
    position: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), init=False
    )

    stage: Mapped["CropPhenologyStage"] = relationship(
        back_populates="recommendations", default=None, repr=False
    )


class CropStageMedia(Base):
    """Photo ou document rattaché à une observation ou à un stade."""

    __tablename__ = "crop_stage_media"

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    observation_id: Mapped[int | None] = mapped_column(
        ForeignKey("crop_stage_observation.id", ondelete="CASCADE"),
        default=None,
    )
    stage_id: Mapped[int | None] = mapped_column(
        ForeignKey("crop_phenology_stage.id", ondelete="SET NULL"), default=None
    )
    kind: Mapped[StageMediaKind] = mapped_column(
        Enum(StageMediaKind, native_enum=False, length=32),
        default=StageMediaKind.PHOTO,
    )
    # Nom de fichier dans le répertoire d'upload Reflex (jamais un chemin dur).
    filename: Mapped[str] = mapped_column(String(240), default="")
    caption: Mapped[str] = mapped_column(String(240), default="")
    author: Mapped[str] = mapped_column(String(120), default="")
    captured_on: Mapped[datetime.date | None] = mapped_column(
        Date, default=None
    )
    position: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), init=False
    )

    observation: Mapped["CropStageObservation | None"] = relationship(
        back_populates="media", default=None, repr=False
    )


class EquipmentUsageLog(Base):
    """Relevé d'utilisation d'un engin (compteur, carburant, chantier)."""

    __tablename__ = "equipment_usage_log"

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    equipment_id: Mapped[int] = mapped_column(
        ForeignKey("equipment.id", ondelete="CASCADE")
    )
    employee_id: Mapped[int | None] = mapped_column(
        ForeignKey("employee.id", ondelete="SET NULL"), default=None
    )
    intervention_id: Mapped[int | None] = mapped_column(
        ForeignKey("intervention.id", ondelete="SET NULL"), default=None
    )
    used_on: Mapped[datetime.date | None] = mapped_column(Date, default=None)
    counter_start: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    counter_end: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    hours_used: Mapped[float] = mapped_column(Numeric(8, 2), default=0)
    fuel_liters: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    notes: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), init=False
    )

    equipment: Mapped["Equipment"] = relationship(
        back_populates="usage_logs", default=None, repr=False
    )


# ---------------------------------------------------------------------------
# Socle utilisateurs, rôles, permissions et sécurité (CMS² AgriPro)
# ---------------------------------------------------------------------------


class FunctionFamily(str, enum.Enum):
    """Famille métier d'une fonction agricole."""

    DIRECTION = "direction"
    PRODUCTION = "production"
    TERRAIN = "terrain"
    LOGISTIQUE = "logistique"
    ADMINISTRATION = "administration"


class UserStatus(str, enum.Enum):
    ACTIF = "actif"
    INACTIF = "inactif"
    SUSPENDU = "suspendu"
    ARCHIVE = "archive"
    EN_ATTENTE = "en_attente"


class MfaMethod(str, enum.Enum):
    AUCUNE = "aucune"
    SMS = "sms"
    APPLICATION = "application"
    EMAIL = "email"
    CLE_MATERIELLE = "cle_materielle"


class ScopeKind(str, enum.Enum):
    """Granularité du périmètre agricole d'une autorisation."""

    EXPLOITATION = "exploitation"
    SITE = "site"
    SECTEUR = "secteur"
    PARCELLE = "parcelle"
    CULTURE = "culture"
    EQUIPE = "equipe"
    ACTIVITE = "activite"
    CAMPAGNE = "campagne"
    PERSONNEL = "personnel"


class TeamStatus(str, enum.Enum):
    ACTIVE = "active"
    SUSPENDUE = "suspendue"
    ARCHIVEE = "archivee"


class DelegationStatus(str, enum.Enum):
    PLANIFIEE = "planifiee"
    ACTIVE = "active"
    EXPIREE = "expiree"
    REVOQUEE = "revoquee"


class SessionStatus(str, enum.Enum):
    ACTIVE = "active"
    EXPIREE = "expiree"
    REVOQUEE = "revoquee"


class ActivityKind(str, enum.Enum):
    CONNEXION = "connexion"
    DECONNEXION = "deconnexion"
    CREATION = "creation"
    MODIFICATION = "modification"
    SUPPRESSION = "suppression"
    AFFECTATION = "affectation"
    VALIDATION = "validation"
    ROLE = "role"
    PERMISSION = "permission"
    DELEGATION = "delegation"
    REFUS = "refus"
    CONSULTATION = "consultation"


class AppFunction(Base):
    """Fonction agricole réelle (métier ou poste occupé)."""

    __tablename__ = "app_function"
    __table_args__ = (UniqueConstraint("key", name="uq_app_function_key"),)

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    key: Mapped[str] = mapped_column(String(80))
    name: Mapped[str] = mapped_column(String(160))
    family: Mapped[FunctionFamily] = mapped_column(
        Enum(FunctionFamily, native_enum=False, length=32),
        default=FunctionFamily.TERRAIN,
    )
    mission: Mapped[str] = mapped_column(Text, default="")
    responsibilities: Mapped[str] = mapped_column(Text, default="")
    default_role_key: Mapped[str] = mapped_column(String(60), default="")
    icon: Mapped[str] = mapped_column(String(40), default="user")
    color_hex: Mapped[str] = mapped_column(String(9), default="#a3e635")
    position: Mapped[int] = mapped_column(default=0)
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), init=False
    )


class AppRole(Base):
    """Rôle applicatif : niveau de responsabilité dans AgriPro."""

    __tablename__ = "app_role"
    __table_args__ = (UniqueConstraint("key", name="uq_app_role_key"),)

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    key: Mapped[str] = mapped_column(String(60))
    name: Mapped[str] = mapped_column(String(160))
    level: Mapped[int] = mapped_column(default=10)
    tagline: Mapped[str] = mapped_column(String(240), default="")
    description: Mapped[str] = mapped_column(Text, default="")
    icon: Mapped[str] = mapped_column(String(40), default="shield")
    color_hex: Mapped[str] = mapped_column(String(9), default="#a3e635")
    is_system: Mapped[bool] = mapped_column(default=False)
    position: Mapped[int] = mapped_column(default=0)
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), init=False
    )


class AppPermission(Base):
    """Permission granulaire : une action sur un module AgriPro."""

    __tablename__ = "app_permission"
    __table_args__ = (UniqueConstraint("key", name="uq_app_permission_key"),)

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    key: Mapped[str] = mapped_column(String(120))
    module: Mapped[str] = mapped_column(String(60))
    action: Mapped[str] = mapped_column(String(40))
    label: Mapped[str] = mapped_column(String(200), default="")
    description: Mapped[str] = mapped_column(Text, default="")
    module_route: Mapped[str] = mapped_column(String(160), default="/")
    icon: Mapped[str] = mapped_column(String(40), default="key-round")
    is_sensitive: Mapped[bool] = mapped_column(default=False)
    position: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), init=False
    )


class RolePermission(Base):
    """Matrice RBAC : permission accordée à un rôle, avec granularité."""

    __tablename__ = "role_permission"
    __table_args__ = (
        UniqueConstraint(
            "role_id", "permission_id", name="uq_role_permission_pair"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    role_id: Mapped[int] = mapped_column(
        ForeignKey("app_role.id", ondelete="CASCADE")
    )
    permission_id: Mapped[int] = mapped_column(
        ForeignKey("app_permission.id", ondelete="CASCADE")
    )
    scope_kind: Mapped[ScopeKind] = mapped_column(
        Enum(ScopeKind, native_enum=False, length=32),
        default=ScopeKind.EXPLOITATION,
    )
    is_granted: Mapped[bool] = mapped_column(default=True)
    notes: Mapped[str] = mapped_column(Text, default="")


class FarmTeam(Base):
    """Équipe agricole opérationnelle."""

    __tablename__ = "farm_team"
    __table_args__ = (UniqueConstraint("key", name="uq_farm_team_key"),)

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    key: Mapped[str] = mapped_column(String(80))
    name: Mapped[str] = mapped_column(String(160))
    code: Mapped[str] = mapped_column(String(40), default="")
    leader_id: Mapped[int | None] = mapped_column(
        ForeignKey("app_user.id", ondelete="SET NULL"), default=None
    )
    function_id: Mapped[int | None] = mapped_column(
        ForeignKey("app_function.id", ondelete="SET NULL"), default=None
    )
    activity: Mapped[str] = mapped_column(String(160), default="")
    schedule: Mapped[str] = mapped_column(String(160), default="")
    farm_key: Mapped[str] = mapped_column(String(80), default="")
    sector: Mapped[str] = mapped_column(String(80), default="")
    status: Mapped[TeamStatus] = mapped_column(
        Enum(TeamStatus, native_enum=False, length=32),
        default=TeamStatus.ACTIVE,
    )
    icon: Mapped[str] = mapped_column(String(40), default="users")
    color_hex: Mapped[str] = mapped_column(String(9), default="#a3e635")
    notes: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), init=False
    )


class AppUser(Base):
    """Utilisateur AgriPro : personne travaillant dans l'exploitation."""

    __tablename__ = "app_user"
    __table_args__ = (UniqueConstraint("matricule", name="uq_app_user_code"),)

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    matricule: Mapped[str] = mapped_column(String(40))
    first_name: Mapped[str] = mapped_column(String(80))
    last_name: Mapped[str] = mapped_column(String(80))
    email: Mapped[str] = mapped_column(String(160), default="")
    phone: Mapped[str] = mapped_column(String(40), default="")
    address: Mapped[str] = mapped_column(String(240), default="")
    photo_seed: Mapped[str] = mapped_column(String(120), default="")
    function_id: Mapped[int | None] = mapped_column(
        ForeignKey("app_function.id", ondelete="SET NULL"), default=None
    )
    primary_role_id: Mapped[int | None] = mapped_column(
        ForeignKey("app_role.id", ondelete="SET NULL"), default=None
    )
    team_id: Mapped[int | None] = mapped_column(
        ForeignKey("farm_team.id", ondelete="SET NULL"), default=None
    )
    manager_id: Mapped[int | None] = mapped_column(
        ForeignKey("app_user.id", ondelete="SET NULL"), default=None
    )
    employee_id: Mapped[int | None] = mapped_column(
        ForeignKey("employee.id", ondelete="SET NULL"), default=None
    )
    farm_key: Mapped[str] = mapped_column(String(80), default="")
    sector: Mapped[str] = mapped_column(String(80), default="")
    status: Mapped[UserStatus] = mapped_column(
        Enum(UserStatus, native_enum=False, length=32),
        default=UserStatus.ACTIF,
    )
    hired_on: Mapped[datetime.date | None] = mapped_column(Date, default=None)
    last_login_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), default=None
    )
    mfa_enabled: Mapped[bool] = mapped_column(default=False)
    mfa_method: Mapped[MfaMethod] = mapped_column(
        Enum(MfaMethod, native_enum=False, length=32), default=MfaMethod.AUCUNE
    )
    notes: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), init=False
    )


class UserRole(Base):
    """Rôle attribué à un utilisateur (plusieurs rôles possibles)."""

    __tablename__ = "user_role"
    __table_args__ = (
        UniqueConstraint("user_id", "role_id", name="uq_user_role_pair"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("app_user.id", ondelete="CASCADE")
    )
    role_id: Mapped[int] = mapped_column(
        ForeignKey("app_role.id", ondelete="CASCADE")
    )
    is_primary: Mapped[bool] = mapped_column(default=False)
    granted_by: Mapped[str] = mapped_column(String(120), default="")
    granted_on: Mapped[datetime.date | None] = mapped_column(Date, default=None)
    notes: Mapped[str] = mapped_column(Text, default="")


class AccessScope(Base):
    """Périmètre agricole d'un utilisateur (exploitation → parcelle)."""

    __tablename__ = "access_scope"

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("app_user.id", ondelete="CASCADE")
    )
    scope_kind: Mapped[ScopeKind] = mapped_column(
        Enum(ScopeKind, native_enum=False, length=32),
        default=ScopeKind.EXPLOITATION,
    )
    farm_key: Mapped[str] = mapped_column(String(80), default="")
    site: Mapped[str] = mapped_column(String(120), default="")
    sector: Mapped[str] = mapped_column(String(80), default="")
    parcel_id: Mapped[int | None] = mapped_column(
        ForeignKey("parcel.id", ondelete="CASCADE"), default=None
    )
    crop_id: Mapped[int | None] = mapped_column(
        ForeignKey("crop.id", ondelete="SET NULL"), default=None
    )
    team_id: Mapped[int | None] = mapped_column(
        ForeignKey("farm_team.id", ondelete="SET NULL"), default=None
    )
    activity: Mapped[str] = mapped_column(String(120), default="")
    season: Mapped[str] = mapped_column(String(40), default="")
    is_readonly: Mapped[bool] = mapped_column(default=False)
    note: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), init=False
    )


class TeamMember(Base):
    """Appartenance d'un utilisateur à une équipe agricole."""

    __tablename__ = "team_member"
    __table_args__ = (
        UniqueConstraint("team_id", "user_id", name="uq_team_member_pair"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    team_id: Mapped[int] = mapped_column(
        ForeignKey("farm_team.id", ondelete="CASCADE")
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("app_user.id", ondelete="CASCADE")
    )
    role_in_team: Mapped[str] = mapped_column(String(120), default="Membre")
    joined_on: Mapped[datetime.date | None] = mapped_column(Date, default=None)
    notes: Mapped[str] = mapped_column(Text, default="")


class UserAssignment(Base):
    """Affectation opérationnelle : exploitation → secteur → parcelle → équipe."""

    __tablename__ = "user_assignment"

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("app_user.id", ondelete="CASCADE")
    )
    farm_key: Mapped[str] = mapped_column(String(80), default="")
    sector: Mapped[str] = mapped_column(String(80), default="")
    parcel_id: Mapped[int | None] = mapped_column(
        ForeignKey("parcel.id", ondelete="CASCADE"), default=None
    )
    crop_id: Mapped[int | None] = mapped_column(
        ForeignKey("crop.id", ondelete="SET NULL"), default=None
    )
    team_id: Mapped[int | None] = mapped_column(
        ForeignKey("farm_team.id", ondelete="SET NULL"), default=None
    )
    activity: Mapped[str] = mapped_column(String(120), default="")
    season: Mapped[str] = mapped_column(String(40), default="")
    is_responsible: Mapped[bool] = mapped_column(default=False)
    start_date: Mapped[datetime.date | None] = mapped_column(Date, default=None)
    end_date: Mapped[datetime.date | None] = mapped_column(Date, default=None)
    notes: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), init=False
    )


class RoleDelegation(Base):
    """Délégation temporaire d'un rôle ou d'une permission unitaire."""

    __tablename__ = "role_delegation"

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    delegator_id: Mapped[int] = mapped_column(
        ForeignKey("app_user.id", ondelete="CASCADE")
    )
    delegate_id: Mapped[int] = mapped_column(
        ForeignKey("app_user.id", ondelete="CASCADE")
    )
    role_id: Mapped[int | None] = mapped_column(
        ForeignKey("app_role.id", ondelete="SET NULL"), default=None
    )
    permission_id: Mapped[int | None] = mapped_column(
        ForeignKey("app_permission.id", ondelete="SET NULL"), default=None
    )
    scope_kind: Mapped[ScopeKind] = mapped_column(
        Enum(ScopeKind, native_enum=False, length=32),
        default=ScopeKind.EXPLOITATION,
    )
    parcel_id: Mapped[int | None] = mapped_column(
        ForeignKey("parcel.id", ondelete="SET NULL"), default=None
    )
    team_id: Mapped[int | None] = mapped_column(
        ForeignKey("farm_team.id", ondelete="SET NULL"), default=None
    )
    reason: Mapped[str] = mapped_column(Text, default="")
    authorized_by: Mapped[str] = mapped_column(String(120), default="")
    start_date: Mapped[datetime.date | None] = mapped_column(Date, default=None)
    end_date: Mapped[datetime.date | None] = mapped_column(Date, default=None)
    status: Mapped[DelegationStatus] = mapped_column(
        Enum(DelegationStatus, native_enum=False, length=32),
        default=DelegationStatus.PLANIFIEE,
    )
    notes: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), init=False
    )


class UserSession(Base):
    """Session applicative représentée, avec état MFA (jeton jamais en clair)."""

    __tablename__ = "user_session"
    __table_args__ = (
        UniqueConstraint("token_hash", name="uq_user_session_token"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("app_user.id", ondelete="CASCADE")
    )
    token_hash: Mapped[str] = mapped_column(String(128))
    device: Mapped[str] = mapped_column(String(120), default="")
    ip_address: Mapped[str] = mapped_column(String(60), default="")
    user_agent: Mapped[str] = mapped_column(String(240), default="")
    mfa_passed: Mapped[bool] = mapped_column(default=False)
    mfa_method: Mapped[MfaMethod] = mapped_column(
        Enum(MfaMethod, native_enum=False, length=32), default=MfaMethod.AUCUNE
    )
    status: Mapped[SessionStatus] = mapped_column(
        Enum(SessionStatus, native_enum=False, length=32),
        default=SessionStatus.ACTIVE,
    )
    started_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), default=None
    )
    last_seen_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), default=None
    )
    expires_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), default=None
    )
    notes: Mapped[str] = mapped_column(Text, default="")


class ActivityLog(Base):
    """Journal d'activité et d'audit : utilisateur → action → objet → date."""

    __tablename__ = "activity_log"

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("app_user.id", ondelete="SET NULL"), default=None
    )
    actor_label: Mapped[str] = mapped_column(String(160), default="Système")
    kind: Mapped[ActivityKind] = mapped_column(
        Enum(ActivityKind, native_enum=False, length=32),
        default=ActivityKind.CONSULTATION,
    )
    module: Mapped[str] = mapped_column(String(60), default="")
    action: Mapped[str] = mapped_column(String(40), default="")
    object_type: Mapped[str] = mapped_column(String(60), default="")
    object_ref: Mapped[str] = mapped_column(String(200), default="")
    object_id: Mapped[int] = mapped_column(default=0)
    summary: Mapped[str] = mapped_column(Text, default="")
    scope_label: Mapped[str] = mapped_column(String(160), default="")
    parcel_id: Mapped[int | None] = mapped_column(
        ForeignKey("parcel.id", ondelete="SET NULL"), default=None
    )
    team_id: Mapped[int | None] = mapped_column(
        ForeignKey("farm_team.id", ondelete="SET NULL"), default=None
    )
    ip_address: Mapped[str] = mapped_column(String(60), default="")
    is_sensitive: Mapped[bool] = mapped_column(default=False)
    occurred_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), default=None
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), init=False
    )


# ---------------------------------------------------------------------------
# CRM & Partenaires : socle métier persistant (clients, fournisseurs, tiers)
# ---------------------------------------------------------------------------


class PartnerKind(str, enum.Enum):
    """Nature commerciale d'un tiers de l'exploitation."""

    CLIENT = "client"
    FOURNISSEUR = "fournisseur"
    MIXTE = "mixte"
    TRANSPORTEUR = "transporteur"
    PRESTATAIRE = "prestataire"
    COOPERATIVE = "cooperative"
    GROSSISTE = "grossiste"
    DISTRIBUTEUR = "distributeur"
    REVENDEUR = "revendeur"
    AUTRE = "autre"


class PartnerLegalForm(str, enum.Enum):
    """Forme juridique déclarée du tiers."""

    PARTICULIER = "particulier"
    ENTREPRISE = "entreprise"
    COOPERATIVE = "cooperative"
    ASSOCIATION = "association"
    ADMINISTRATION = "administration"
    AUTRE = "autre"


class PartnerStatus(str, enum.Enum):
    """Cycle de vie d'un tiers : l'archivage remplace la suppression."""

    ACTIF = "actif"
    INACTIF = "inactif"
    BLOQUE = "bloque"
    PROSPECT = "prospect"
    ARCHIVE = "archive"


class SupplierDomain(str, enum.Enum):
    """Catégorie d'approvisionnement d'un fournisseur agricole."""

    SEMENCES = "semences"
    ENGRAIS = "engrais"
    PHYTOSANITAIRE = "phytosanitaire"
    MATERIEL = "materiel"
    PIECES = "pieces"
    CARBURANT = "carburant"
    IRRIGATION = "irrigation"
    EMBALLAGE = "emballage"
    TRANSPORT = "transport"
    SERVICES = "services"
    MAINTENANCE = "maintenance"
    ENERGIE = "energie"
    AUTRE = "autre"


class SaleStatus(str, enum.Enum):
    BROUILLON = "brouillon"
    CONFIRMEE = "confirmee"
    PREPAREE = "preparee"
    LIVREE = "livree"
    FACTUREE = "facturee"
    PARTIELLEMENT_PAYEE = "partiellement_payee"
    PAYEE = "payee"
    ANNULEE = "annulee"


class PurchaseStatus(str, enum.Enum):
    BROUILLON = "brouillon"
    COMMANDEE = "commandee"
    RECEPTIONNEE = "receptionnee"
    FACTUREE = "facturee"
    PARTIELLEMENT_PAYEE = "partiellement_payee"
    PAYEE = "payee"
    ANNULEE = "annulee"


class InvoiceKind(str, enum.Enum):
    """Sens de la facture : émise au client ou reçue du fournisseur."""

    VENTE = "vente"
    ACHAT = "achat"
    AVOIR_VENTE = "avoir_vente"
    AVOIR_ACHAT = "avoir_achat"


class InvoiceStatus(str, enum.Enum):
    BROUILLON = "brouillon"
    EMISE = "emise"
    PARTIELLEMENT_PAYEE = "partiellement_payee"
    PAYEE = "payee"
    EN_RETARD = "en_retard"
    ANNULEE = "annulee"


class SettlementStatus(str, enum.Enum):
    """Statut d'une créance client ou d'une dette fournisseur."""

    OUVERTE = "ouverte"
    PARTIELLE = "partielle"
    REGLEE = "reglee"
    EN_RETARD = "en_retard"
    LITIGE = "litige"
    IRRECOUVRABLE = "irrecouvrable"


class PaymentDirection(str, enum.Enum):
    ENCAISSEMENT = "encaissement"
    DECAISSEMENT = "decaissement"


class CrmDocumentKind(str, enum.Enum):
    CONTRAT = "contrat"
    FACTURE = "facture"
    BON_COMMANDE = "bon_commande"
    BON_LIVRAISON = "bon_livraison"
    DEVIS = "devis"
    CERTIFICAT = "certificat"
    DOCUMENT_FISCAL = "document_fiscal"
    REGISTRE_COMMERCE = "registre_commerce"
    CONVENTION = "convention"
    CORRESPONDANCE = "correspondance"
    PHOTO = "photo"
    AUTRE = "autre"


class CrmEventKind(str, enum.Enum):
    """Nature d'un événement de l'historique 360° d'un tiers."""

    CREATION = "creation"
    MISE_A_JOUR = "mise_a_jour"
    CONTACT = "contact"
    VENTE = "vente"
    ACHAT = "achat"
    LIVRAISON = "livraison"
    FACTURE = "facture"
    PAIEMENT = "paiement"
    RELANCE = "relance"
    DOCUMENT = "document"
    SCORE = "score"
    ALERTE = "alerte"
    ARCHIVAGE = "archivage"
    AUTRE = "autre"


class CrmScoreKind(str, enum.Enum):
    CLIENT = "client"
    FOURNISSEUR = "fournisseur"


class CrmScoreGrade(str, enum.Enum):
    EXCELLENT = "excellent"
    BON = "bon"
    MOYEN = "moyen"
    FRAGILE = "fragile"
    RISQUE = "risque"


class CrmPartner(Base):
    """Tiers commercial : client, fournisseur, mixte ou autre partenaire.

    Une seule table normalisée porte tous les tiers (le `kind` distingue les
    clients des fournisseurs et des partenaires mixtes) afin d'éviter la
    duplication d'identité, d'adresse et de conditions commerciales.
    """

    __tablename__ = "crm_partner"
    __table_args__ = (UniqueConstraint("code", name="uq_crm_partner_code"),)

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    code: Mapped[str] = mapped_column(String(40))
    legal_name: Mapped[str] = mapped_column(String(200))
    kind: Mapped[PartnerKind] = mapped_column(
        Enum(PartnerKind, native_enum=False, length=32),
        default=PartnerKind.CLIENT,
    )
    legal_form: Mapped[PartnerLegalForm] = mapped_column(
        Enum(PartnerLegalForm, native_enum=False, length=32),
        default=PartnerLegalForm.ENTREPRISE,
    )
    status: Mapped[PartnerStatus] = mapped_column(
        Enum(PartnerStatus, native_enum=False, length=32),
        default=PartnerStatus.ACTIF,
    )
    trade_name: Mapped[str] = mapped_column(String(200), default="")
    # --- Identifiants fiscaux et administratifs -----------------------
    tax_id: Mapped[str] = mapped_column(String(60), default="")
    trade_register: Mapped[str] = mapped_column(String(60), default="")
    nif: Mapped[str] = mapped_column(String(60), default="")
    nis: Mapped[str] = mapped_column(String(60), default="")
    # --- Coordonnées --------------------------------------------------
    address: Mapped[str] = mapped_column(String(240), default="")
    wilaya: Mapped[str] = mapped_column(String(120), default="")
    commune: Mapped[str] = mapped_column(String(120), default="")
    postal_code: Mapped[str] = mapped_column(String(20), default="")
    country: Mapped[str] = mapped_column(String(80), default="Algérie")
    phone: Mapped[str] = mapped_column(String(40), default="")
    phone_secondary: Mapped[str] = mapped_column(String(40), default="")
    whatsapp: Mapped[str] = mapped_column(String(40), default="")
    email: Mapped[str] = mapped_column(String(160), default="")
    website: Mapped[str] = mapped_column(String(200), default="")
    latitude: Mapped[float] = mapped_column(Numeric(9, 6), default=0)
    longitude: Mapped[float] = mapped_column(Numeric(9, 6), default=0)
    # --- Conditions commerciales --------------------------------------
    category: Mapped[str] = mapped_column(String(120), default="")
    segment: Mapped[str] = mapped_column(String(120), default="")
    supplier_domain: Mapped[SupplierDomain] = mapped_column(
        Enum(SupplierDomain, native_enum=False, length=32),
        default=SupplierDomain.AUTRE,
    )
    account_manager_id: Mapped[int | None] = mapped_column(
        ForeignKey("employee.id", ondelete="SET NULL"), default=None
    )
    payment_terms: Mapped[str] = mapped_column(String(160), default="")
    payment_delay_days: Mapped[int] = mapped_column(default=30)
    credit_limit: Mapped[float] = mapped_column(Numeric(14, 2), default=0)
    default_discount_percent: Mapped[float] = mapped_column(
        Numeric(5, 2), default=0
    )
    default_vat_rate: Mapped[float] = mapped_column(Numeric(5, 2), default=19)
    currency: Mapped[str] = mapped_column(String(10), default="DZD")
    preferred_payment_method: Mapped[PaymentMethod] = mapped_column(
        Enum(PaymentMethod, native_enum=False, length=32),
        default=PaymentMethod.VIREMENT,
    )
    # --- Ancrage agricole (réutilisation des modèles existants) --------
    main_parcel_id: Mapped[int | None] = mapped_column(
        ForeignKey("parcel.id", ondelete="SET NULL"), default=None
    )
    main_culture_id: Mapped[int | None] = mapped_column(
        ForeignKey("crop_culture.id", ondelete="SET NULL"), default=None
    )
    main_product_id: Mapped[int | None] = mapped_column(
        ForeignKey("product.id", ondelete="SET NULL"), default=None
    )
    # --- Suivi ---------------------------------------------------------
    primary_contact_name: Mapped[str] = mapped_column(String(160), default="")
    primary_contact_role: Mapped[str] = mapped_column(String(120), default="")
    first_deal_on: Mapped[datetime.date | None] = mapped_column(
        Date, default=None
    )
    last_activity_on: Mapped[datetime.date | None] = mapped_column(
        Date, default=None
    )
    score_value: Mapped[int] = mapped_column(default=0)
    is_archived: Mapped[bool] = mapped_column(default=False)
    archived_on: Mapped[datetime.date | None] = mapped_column(
        Date, default=None
    )
    archive_reason: Mapped[str] = mapped_column(Text, default="")
    tags: Mapped[str] = mapped_column(Text, default="")
    notes: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), init=False
    )

    # NB : les relations scalaires du CRM sont déclarées `init=False`. Un
    # `default=None` placerait explicitement la relation à None dans le
    # constructeur dataclass, ce qui écraserait la clé étrangère fournie
    # (`partner_id=...`) au moment du flush et produirait un NULL invalide.
    contacts: Mapped[list["CrmContact"]] = relationship(
        back_populates="partner", default_factory=list, repr=False
    )
    sales: Mapped[list["CrmSale"]] = relationship(
        back_populates="partner", default_factory=list, repr=False
    )
    purchases: Mapped[list["CrmPurchase"]] = relationship(
        back_populates="partner", default_factory=list, repr=False
    )
    invoices: Mapped[list["CrmInvoice"]] = relationship(
        back_populates="partner", default_factory=list, repr=False
    )
    payments: Mapped[list["CrmPayment"]] = relationship(
        back_populates="partner", default_factory=list, repr=False
    )
    documents: Mapped[list["CrmDocument"]] = relationship(
        back_populates="partner", default_factory=list, repr=False
    )
    events: Mapped[list["CrmEvent"]] = relationship(
        back_populates="partner", default_factory=list, repr=False
    )
    scores: Mapped[list["CrmScore"]] = relationship(
        back_populates="partner", default_factory=list, repr=False
    )


class CrmContact(Base):
    """Contact physique rattaché à un tiers (plusieurs par partenaire)."""

    __tablename__ = "crm_contact"

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    partner_id: Mapped[int] = mapped_column(
        ForeignKey("crm_partner.id", ondelete="CASCADE")
    )
    last_name: Mapped[str] = mapped_column(String(80))
    first_name: Mapped[str] = mapped_column(String(80), default="")
    role: Mapped[str] = mapped_column(String(120), default="")
    phone: Mapped[str] = mapped_column(String(40), default="")
    mobile: Mapped[str] = mapped_column(String(40), default="")
    whatsapp: Mapped[str] = mapped_column(String(40), default="")
    email: Mapped[str] = mapped_column(String(160), default="")
    is_primary: Mapped[bool] = mapped_column(default=False)
    is_archived: Mapped[bool] = mapped_column(default=False)
    language: Mapped[str] = mapped_column(String(40), default="")
    notes: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), init=False
    )

    partner: Mapped["CrmPartner"] = relationship(
        back_populates="contacts", init=False, repr=False
    )


class CrmSale(Base):
    """Transaction de vente à un client, ancrée dans le cycle agricole."""

    __tablename__ = "crm_sale"
    __table_args__ = (UniqueConstraint("code", name="uq_crm_sale_code"),)

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    partner_id: Mapped[int] = mapped_column(
        ForeignKey("crm_partner.id", ondelete="RESTRICT")
    )
    code: Mapped[str] = mapped_column(String(40))
    status: Mapped[SaleStatus] = mapped_column(
        Enum(SaleStatus, native_enum=False, length=32),
        default=SaleStatus.BROUILLON,
    )
    sale_date: Mapped[datetime.date | None] = mapped_column(Date, default=None)
    delivery_date: Mapped[datetime.date | None] = mapped_column(
        Date, default=None
    )
    season: Mapped[str] = mapped_column(String(40), default="")
    label: Mapped[str] = mapped_column(String(200), default="")
    delivery_note: Mapped[str] = mapped_column(String(120), default="")
    order_reference: Mapped[str] = mapped_column(String(120), default="")
    # Liens agricoles optionnels (aucune duplication de données agronomiques).
    parcel_id: Mapped[int | None] = mapped_column(
        ForeignKey("parcel.id", ondelete="SET NULL"), default=None
    )
    crop_id: Mapped[int | None] = mapped_column(
        ForeignKey("crop.id", ondelete="SET NULL"), default=None
    )
    harvest_id: Mapped[int | None] = mapped_column(
        ForeignKey("harvest.id", ondelete="SET NULL"), default=None
    )
    culture_id: Mapped[int | None] = mapped_column(
        ForeignKey("crop_culture.id", ondelete="SET NULL"), default=None
    )
    catalog_variety_id: Mapped[int | None] = mapped_column(
        ForeignKey("crop_catalog_variety.id", ondelete="SET NULL"), default=None
    )
    currency: Mapped[str] = mapped_column(String(10), default="DZD")
    payment_method: Mapped[PaymentMethod] = mapped_column(
        Enum(PaymentMethod, native_enum=False, length=32),
        default=PaymentMethod.VIREMENT,
    )
    discount_percent: Mapped[float] = mapped_column(Numeric(5, 2), default=0)
    amount_ht: Mapped[float] = mapped_column(Numeric(14, 2), default=0)
    vat_amount: Mapped[float] = mapped_column(Numeric(14, 2), default=0)
    amount_ttc: Mapped[float] = mapped_column(Numeric(14, 2), default=0)
    paid_amount: Mapped[float] = mapped_column(Numeric(14, 2), default=0)
    transport_cost: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    is_archived: Mapped[bool] = mapped_column(default=False)
    notes: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), init=False
    )

    partner: Mapped["CrmPartner"] = relationship(
        back_populates="sales", init=False, repr=False
    )
    items: Mapped[list["CrmSaleItem"]] = relationship(
        back_populates="sale", default_factory=list, repr=False
    )


class CrmSaleItem(Base):
    """Ligne d'une vente (produit récolté ou intrant revendu)."""

    __tablename__ = "crm_sale_item"

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    sale_id: Mapped[int] = mapped_column(
        ForeignKey("crm_sale.id", ondelete="CASCADE")
    )
    label: Mapped[str] = mapped_column(String(200))
    position: Mapped[int] = mapped_column(default=0)
    product_id: Mapped[int | None] = mapped_column(
        ForeignKey("product.id", ondelete="SET NULL"), default=None
    )
    harvest_id: Mapped[int | None] = mapped_column(
        ForeignKey("harvest.id", ondelete="SET NULL"), default=None
    )
    crop_id: Mapped[int | None] = mapped_column(
        ForeignKey("crop.id", ondelete="SET NULL"), default=None
    )
    parcel_id: Mapped[int | None] = mapped_column(
        ForeignKey("parcel.id", ondelete="SET NULL"), default=None
    )
    catalog_variety_id: Mapped[int | None] = mapped_column(
        ForeignKey("crop_catalog_variety.id", ondelete="SET NULL"), default=None
    )
    quantity: Mapped[float] = mapped_column(Numeric(14, 3), default=0)
    unit: Mapped[str] = mapped_column(String(20), default="t")
    unit_price: Mapped[float] = mapped_column(Numeric(14, 2), default=0)
    discount_percent: Mapped[float] = mapped_column(Numeric(5, 2), default=0)
    vat_rate: Mapped[float] = mapped_column(Numeric(5, 2), default=19)
    amount_ht: Mapped[float] = mapped_column(Numeric(14, 2), default=0)
    vat_amount: Mapped[float] = mapped_column(Numeric(14, 2), default=0)
    amount_ttc: Mapped[float] = mapped_column(Numeric(14, 2), default=0)
    quality_grade: Mapped[str] = mapped_column(String(60), default="")
    notes: Mapped[str] = mapped_column(Text, default="")

    sale: Mapped["CrmSale"] = relationship(
        back_populates="items", init=False, repr=False
    )


class CrmPurchase(Base):
    """Transaction d'achat auprès d'un fournisseur."""

    __tablename__ = "crm_purchase"
    __table_args__ = (UniqueConstraint("code", name="uq_crm_purchase_code"),)

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    partner_id: Mapped[int] = mapped_column(
        ForeignKey("crm_partner.id", ondelete="RESTRICT")
    )
    code: Mapped[str] = mapped_column(String(40))
    status: Mapped[PurchaseStatus] = mapped_column(
        Enum(PurchaseStatus, native_enum=False, length=32),
        default=PurchaseStatus.BROUILLON,
    )
    purchase_date: Mapped[datetime.date | None] = mapped_column(
        Date, default=None
    )
    received_date: Mapped[datetime.date | None] = mapped_column(
        Date, default=None
    )
    season: Mapped[str] = mapped_column(String(40), default="")
    label: Mapped[str] = mapped_column(String(200), default="")
    order_reference: Mapped[str] = mapped_column(String(120), default="")
    receipt_reference: Mapped[str] = mapped_column(String(120), default="")
    domain: Mapped[SupplierDomain] = mapped_column(
        Enum(SupplierDomain, native_enum=False, length=32),
        default=SupplierDomain.AUTRE,
    )
    # Liens agricoles et logistiques optionnels.
    parcel_id: Mapped[int | None] = mapped_column(
        ForeignKey("parcel.id", ondelete="SET NULL"), default=None
    )
    crop_id: Mapped[int | None] = mapped_column(
        ForeignKey("crop.id", ondelete="SET NULL"), default=None
    )
    intervention_id: Mapped[int | None] = mapped_column(
        ForeignKey("intervention.id", ondelete="SET NULL"), default=None
    )
    equipment_id: Mapped[int | None] = mapped_column(
        ForeignKey("equipment.id", ondelete="SET NULL"), default=None
    )
    maintenance_id: Mapped[int | None] = mapped_column(
        ForeignKey("maintenance_operation.id", ondelete="SET NULL"),
        default=None,
    )
    expense_id: Mapped[int | None] = mapped_column(
        ForeignKey("expense.id", ondelete="SET NULL"), default=None
    )
    currency: Mapped[str] = mapped_column(String(10), default="DZD")
    payment_method: Mapped[PaymentMethod] = mapped_column(
        Enum(PaymentMethod, native_enum=False, length=32),
        default=PaymentMethod.VIREMENT,
    )
    discount_percent: Mapped[float] = mapped_column(Numeric(5, 2), default=0)
    amount_ht: Mapped[float] = mapped_column(Numeric(14, 2), default=0)
    vat_amount: Mapped[float] = mapped_column(Numeric(14, 2), default=0)
    amount_ttc: Mapped[float] = mapped_column(Numeric(14, 2), default=0)
    paid_amount: Mapped[float] = mapped_column(Numeric(14, 2), default=0)
    transport_cost: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    is_archived: Mapped[bool] = mapped_column(default=False)
    notes: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), init=False
    )

    partner: Mapped["CrmPartner"] = relationship(
        back_populates="purchases", init=False, repr=False
    )
    items: Mapped[list["CrmPurchaseItem"]] = relationship(
        back_populates="purchase", default_factory=list, repr=False
    )


class CrmPurchaseItem(Base):
    """Ligne d'achat, reliée si possible au produit d'intrant existant."""

    __tablename__ = "crm_purchase_item"

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    purchase_id: Mapped[int] = mapped_column(
        ForeignKey("crm_purchase.id", ondelete="CASCADE")
    )
    label: Mapped[str] = mapped_column(String(200))
    position: Mapped[int] = mapped_column(default=0)
    product_id: Mapped[int | None] = mapped_column(
        ForeignKey("product.id", ondelete="SET NULL"), default=None
    )
    stock_movement_id: Mapped[int | None] = mapped_column(
        ForeignKey("stock_movement.id", ondelete="SET NULL"), default=None
    )
    parcel_id: Mapped[int | None] = mapped_column(
        ForeignKey("parcel.id", ondelete="SET NULL"), default=None
    )
    crop_id: Mapped[int | None] = mapped_column(
        ForeignKey("crop.id", ondelete="SET NULL"), default=None
    )
    intervention_id: Mapped[int | None] = mapped_column(
        ForeignKey("intervention.id", ondelete="SET NULL"), default=None
    )
    domain: Mapped[SupplierDomain] = mapped_column(
        Enum(SupplierDomain, native_enum=False, length=32),
        default=SupplierDomain.AUTRE,
    )
    quantity: Mapped[float] = mapped_column(Numeric(14, 3), default=0)
    unit: Mapped[str] = mapped_column(String(20), default="u")
    unit_price: Mapped[float] = mapped_column(Numeric(14, 2), default=0)
    discount_percent: Mapped[float] = mapped_column(Numeric(5, 2), default=0)
    vat_rate: Mapped[float] = mapped_column(Numeric(5, 2), default=19)
    amount_ht: Mapped[float] = mapped_column(Numeric(14, 2), default=0)
    vat_amount: Mapped[float] = mapped_column(Numeric(14, 2), default=0)
    amount_ttc: Mapped[float] = mapped_column(Numeric(14, 2), default=0)
    notes: Mapped[str] = mapped_column(Text, default="")

    purchase: Mapped["CrmPurchase"] = relationship(
        back_populates="items", init=False, repr=False
    )


class CrmInvoice(Base):
    """Facture client ou fournisseur, pivot des créances et des dettes."""

    __tablename__ = "crm_invoice"
    __table_args__ = (UniqueConstraint("code", name="uq_crm_invoice_code"),)

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    partner_id: Mapped[int] = mapped_column(
        ForeignKey("crm_partner.id", ondelete="RESTRICT")
    )
    code: Mapped[str] = mapped_column(String(40))
    kind: Mapped[InvoiceKind] = mapped_column(
        Enum(InvoiceKind, native_enum=False, length=32),
        default=InvoiceKind.VENTE,
    )
    status: Mapped[InvoiceStatus] = mapped_column(
        Enum(InvoiceStatus, native_enum=False, length=32),
        default=InvoiceStatus.BROUILLON,
    )
    sale_id: Mapped[int | None] = mapped_column(
        ForeignKey("crm_sale.id", ondelete="SET NULL"), default=None
    )
    purchase_id: Mapped[int | None] = mapped_column(
        ForeignKey("crm_purchase.id", ondelete="SET NULL"), default=None
    )
    external_reference: Mapped[str] = mapped_column(String(120), default="")
    issue_date: Mapped[datetime.date | None] = mapped_column(Date, default=None)
    due_date: Mapped[datetime.date | None] = mapped_column(Date, default=None)
    season: Mapped[str] = mapped_column(String(40), default="")
    currency: Mapped[str] = mapped_column(String(10), default="DZD")
    amount_ht: Mapped[float] = mapped_column(Numeric(14, 2), default=0)
    vat_amount: Mapped[float] = mapped_column(Numeric(14, 2), default=0)
    amount_ttc: Mapped[float] = mapped_column(Numeric(14, 2), default=0)
    paid_amount: Mapped[float] = mapped_column(Numeric(14, 2), default=0)
    remaining_amount: Mapped[float] = mapped_column(Numeric(14, 2), default=0)
    overdue_days: Mapped[int] = mapped_column(default=0)
    is_archived: Mapped[bool] = mapped_column(default=False)
    notes: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), init=False
    )

    partner: Mapped["CrmPartner"] = relationship(
        back_populates="invoices", init=False, repr=False
    )
    items: Mapped[list["CrmInvoiceItem"]] = relationship(
        back_populates="invoice", default_factory=list, repr=False
    )
    payments: Mapped[list["CrmPayment"]] = relationship(
        back_populates="invoice", default_factory=list, repr=False
    )


class CrmInvoiceItem(Base):
    """Ligne de facture, reliée à la ligne de vente ou d'achat d'origine."""

    __tablename__ = "crm_invoice_item"

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    invoice_id: Mapped[int] = mapped_column(
        ForeignKey("crm_invoice.id", ondelete="CASCADE")
    )
    label: Mapped[str] = mapped_column(String(200))
    position: Mapped[int] = mapped_column(default=0)
    sale_item_id: Mapped[int | None] = mapped_column(
        ForeignKey("crm_sale_item.id", ondelete="SET NULL"), default=None
    )
    purchase_item_id: Mapped[int | None] = mapped_column(
        ForeignKey("crm_purchase_item.id", ondelete="SET NULL"), default=None
    )
    product_id: Mapped[int | None] = mapped_column(
        ForeignKey("product.id", ondelete="SET NULL"), default=None
    )
    quantity: Mapped[float] = mapped_column(Numeric(14, 3), default=0)
    unit: Mapped[str] = mapped_column(String(20), default="u")
    unit_price: Mapped[float] = mapped_column(Numeric(14, 2), default=0)
    discount_percent: Mapped[float] = mapped_column(Numeric(5, 2), default=0)
    vat_rate: Mapped[float] = mapped_column(Numeric(5, 2), default=19)
    amount_ht: Mapped[float] = mapped_column(Numeric(14, 2), default=0)
    vat_amount: Mapped[float] = mapped_column(Numeric(14, 2), default=0)
    amount_ttc: Mapped[float] = mapped_column(Numeric(14, 2), default=0)
    notes: Mapped[str] = mapped_column(Text, default="")

    invoice: Mapped["CrmInvoice"] = relationship(
        back_populates="items", init=False, repr=False
    )


class CrmPayment(Base):
    """Encaissement client ou décaissement fournisseur (registre unique)."""

    __tablename__ = "crm_payment"
    __table_args__ = (UniqueConstraint("code", name="uq_crm_payment_code"),)

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    partner_id: Mapped[int] = mapped_column(
        ForeignKey("crm_partner.id", ondelete="RESTRICT")
    )
    code: Mapped[str] = mapped_column(String(40))
    direction: Mapped[PaymentDirection] = mapped_column(
        Enum(PaymentDirection, native_enum=False, length=32),
        default=PaymentDirection.ENCAISSEMENT,
    )
    invoice_id: Mapped[int | None] = mapped_column(
        ForeignKey("crm_invoice.id", ondelete="SET NULL"), default=None
    )
    sale_id: Mapped[int | None] = mapped_column(
        ForeignKey("crm_sale.id", ondelete="SET NULL"), default=None
    )
    purchase_id: Mapped[int | None] = mapped_column(
        ForeignKey("crm_purchase.id", ondelete="SET NULL"), default=None
    )
    paid_on: Mapped[datetime.date | None] = mapped_column(Date, default=None)
    amount: Mapped[float] = mapped_column(Numeric(14, 2), default=0)
    currency: Mapped[str] = mapped_column(String(10), default="DZD")
    method: Mapped[PaymentMethod] = mapped_column(
        Enum(PaymentMethod, native_enum=False, length=32),
        default=PaymentMethod.VIREMENT,
    )
    reference: Mapped[str] = mapped_column(String(120), default="")
    bank: Mapped[str] = mapped_column(String(160), default="")
    cash_desk: Mapped[str] = mapped_column(String(120), default="")
    recorded_by: Mapped[str] = mapped_column(String(120), default="")
    is_archived: Mapped[bool] = mapped_column(default=False)
    comment: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), init=False
    )

    partner: Mapped["CrmPartner"] = relationship(
        back_populates="payments", init=False, repr=False
    )
    invoice: Mapped["CrmInvoice | None"] = relationship(
        back_populates="payments", init=False, repr=False
    )


class CrmReceivable(Base):
    """Créance client dérivée d'une facture de vente."""

    __tablename__ = "crm_receivable"

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    partner_id: Mapped[int] = mapped_column(
        ForeignKey("crm_partner.id", ondelete="CASCADE")
    )
    invoice_id: Mapped[int | None] = mapped_column(
        ForeignKey("crm_invoice.id", ondelete="CASCADE"), default=None
    )
    sale_id: Mapped[int | None] = mapped_column(
        ForeignKey("crm_sale.id", ondelete="SET NULL"), default=None
    )
    status: Mapped[SettlementStatus] = mapped_column(
        Enum(SettlementStatus, native_enum=False, length=32),
        default=SettlementStatus.OUVERTE,
    )
    issue_date: Mapped[datetime.date | None] = mapped_column(Date, default=None)
    due_date: Mapped[datetime.date | None] = mapped_column(Date, default=None)
    amount_due: Mapped[float] = mapped_column(Numeric(14, 2), default=0)
    amount_paid: Mapped[float] = mapped_column(Numeric(14, 2), default=0)
    amount_remaining: Mapped[float] = mapped_column(Numeric(14, 2), default=0)
    overdue_days: Mapped[int] = mapped_column(default=0)
    aging_bucket: Mapped[str] = mapped_column(String(20), default="0-30")
    last_reminder_on: Mapped[datetime.date | None] = mapped_column(
        Date, default=None
    )
    reminder_count: Mapped[int] = mapped_column(default=0)
    is_archived: Mapped[bool] = mapped_column(default=False)
    notes: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), init=False
    )


class CrmPayable(Base):
    """Dette fournisseur dérivée d'une facture d'achat."""

    __tablename__ = "crm_payable"

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    partner_id: Mapped[int] = mapped_column(
        ForeignKey("crm_partner.id", ondelete="CASCADE")
    )
    invoice_id: Mapped[int | None] = mapped_column(
        ForeignKey("crm_invoice.id", ondelete="CASCADE"), default=None
    )
    purchase_id: Mapped[int | None] = mapped_column(
        ForeignKey("crm_purchase.id", ondelete="SET NULL"), default=None
    )
    status: Mapped[SettlementStatus] = mapped_column(
        Enum(SettlementStatus, native_enum=False, length=32),
        default=SettlementStatus.OUVERTE,
    )
    issue_date: Mapped[datetime.date | None] = mapped_column(Date, default=None)
    due_date: Mapped[datetime.date | None] = mapped_column(Date, default=None)
    amount_due: Mapped[float] = mapped_column(Numeric(14, 2), default=0)
    amount_paid: Mapped[float] = mapped_column(Numeric(14, 2), default=0)
    amount_remaining: Mapped[float] = mapped_column(Numeric(14, 2), default=0)
    overdue_days: Mapped[int] = mapped_column(default=0)
    aging_bucket: Mapped[str] = mapped_column(String(20), default="0-30")
    is_archived: Mapped[bool] = mapped_column(default=False)
    notes: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), init=False
    )


class CrmDocument(Base):
    """Document centralisé d'un tiers (fichier dans le dossier d'upload)."""

    __tablename__ = "crm_document"

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    partner_id: Mapped[int] = mapped_column(
        ForeignKey("crm_partner.id", ondelete="CASCADE")
    )
    title: Mapped[str] = mapped_column(String(200))
    kind: Mapped[CrmDocumentKind] = mapped_column(
        Enum(CrmDocumentKind, native_enum=False, length=32),
        default=CrmDocumentKind.AUTRE,
    )
    # Nom de fichier dans le répertoire d'upload Reflex (jamais un chemin dur).
    filename: Mapped[str] = mapped_column(String(240), default="")
    mime_type: Mapped[str] = mapped_column(String(120), default="")
    size_kb: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    reference: Mapped[str] = mapped_column(String(120), default="")
    issued_on: Mapped[datetime.date | None] = mapped_column(Date, default=None)
    expires_on: Mapped[datetime.date | None] = mapped_column(Date, default=None)
    author: Mapped[str] = mapped_column(String(120), default="")
    is_confidential: Mapped[bool] = mapped_column(default=False)
    is_archived: Mapped[bool] = mapped_column(default=False)
    tags: Mapped[str] = mapped_column(Text, default="")
    notes: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), init=False
    )

    partner: Mapped["CrmPartner"] = relationship(
        back_populates="documents", init=False, repr=False
    )
    links: Mapped[list["CrmDocumentLink"]] = relationship(
        back_populates="document", default_factory=list, repr=False
    )


class CrmDocumentLink(Base):
    """Rattachement d'un document à un objet CRM ou agricole existant."""

    __tablename__ = "crm_document_link"

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    document_id: Mapped[int] = mapped_column(
        ForeignKey("crm_document.id", ondelete="CASCADE")
    )
    label: Mapped[str] = mapped_column(String(200), default="")
    sale_id: Mapped[int | None] = mapped_column(
        ForeignKey("crm_sale.id", ondelete="CASCADE"), default=None
    )
    purchase_id: Mapped[int | None] = mapped_column(
        ForeignKey("crm_purchase.id", ondelete="CASCADE"), default=None
    )
    invoice_id: Mapped[int | None] = mapped_column(
        ForeignKey("crm_invoice.id", ondelete="CASCADE"), default=None
    )
    payment_id: Mapped[int | None] = mapped_column(
        ForeignKey("crm_payment.id", ondelete="CASCADE"), default=None
    )
    contact_id: Mapped[int | None] = mapped_column(
        ForeignKey("crm_contact.id", ondelete="SET NULL"), default=None
    )
    parcel_id: Mapped[int | None] = mapped_column(
        ForeignKey("parcel.id", ondelete="SET NULL"), default=None
    )
    crop_id: Mapped[int | None] = mapped_column(
        ForeignKey("crop.id", ondelete="SET NULL"), default=None
    )
    harvest_id: Mapped[int | None] = mapped_column(
        ForeignKey("harvest.id", ondelete="SET NULL"), default=None
    )
    product_id: Mapped[int | None] = mapped_column(
        ForeignKey("product.id", ondelete="SET NULL"), default=None
    )
    intervention_id: Mapped[int | None] = mapped_column(
        ForeignKey("intervention.id", ondelete="SET NULL"), default=None
    )
    module_route: Mapped[str] = mapped_column(String(160), default="")
    position: Mapped[int] = mapped_column(default=0)
    notes: Mapped[str] = mapped_column(Text, default="")

    # `init=False` est impératif : exposer la relation dans le constructeur
    # dataclass y injecterait `document=None`, ce qui écraserait le
    # `document_id` fourni au moment du flush et produirait un NULL invalide.
    document: Mapped["CrmDocument"] = relationship(
        back_populates="links", init=False, repr=False
    )


class CrmEvent(Base):
    """Événement de l'historique 360° d'un tiers (timeline consolidée)."""

    __tablename__ = "crm_event"

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    partner_id: Mapped[int] = mapped_column(
        ForeignKey("crm_partner.id", ondelete="CASCADE")
    )
    kind: Mapped[CrmEventKind] = mapped_column(
        Enum(CrmEventKind, native_enum=False, length=32),
        default=CrmEventKind.AUTRE,
    )
    title: Mapped[str] = mapped_column(String(220), default="")
    summary: Mapped[str] = mapped_column(Text, default="")
    occurred_on: Mapped[datetime.date | None] = mapped_column(
        Date, default=None
    )
    amount: Mapped[float] = mapped_column(Numeric(14, 2), default=0)
    author: Mapped[str] = mapped_column(String(120), default="")
    contact_id: Mapped[int | None] = mapped_column(
        ForeignKey("crm_contact.id", ondelete="SET NULL"), default=None
    )
    sale_id: Mapped[int | None] = mapped_column(
        ForeignKey("crm_sale.id", ondelete="SET NULL"), default=None
    )
    purchase_id: Mapped[int | None] = mapped_column(
        ForeignKey("crm_purchase.id", ondelete="SET NULL"), default=None
    )
    invoice_id: Mapped[int | None] = mapped_column(
        ForeignKey("crm_invoice.id", ondelete="SET NULL"), default=None
    )
    payment_id: Mapped[int | None] = mapped_column(
        ForeignKey("crm_payment.id", ondelete="SET NULL"), default=None
    )
    document_id: Mapped[int | None] = mapped_column(
        ForeignKey("crm_document.id", ondelete="SET NULL"), default=None
    )
    parcel_id: Mapped[int | None] = mapped_column(
        ForeignKey("parcel.id", ondelete="SET NULL"), default=None
    )
    crop_id: Mapped[int | None] = mapped_column(
        ForeignKey("crop.id", ondelete="SET NULL"), default=None
    )
    harvest_id: Mapped[int | None] = mapped_column(
        ForeignKey("harvest.id", ondelete="SET NULL"), default=None
    )
    module_route: Mapped[str] = mapped_column(String(160), default="/crm")
    icon: Mapped[str] = mapped_column(String(40), default="history")
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), init=False
    )

    partner: Mapped["CrmPartner"] = relationship(
        back_populates="events", init=False, repr=False
    )


class CrmScore(Base):
    """Score calculé d'un client ou d'un fournisseur, avec ses composantes."""

    __tablename__ = "crm_score"

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    partner_id: Mapped[int] = mapped_column(
        ForeignKey("crm_partner.id", ondelete="CASCADE")
    )
    kind: Mapped[CrmScoreKind] = mapped_column(
        Enum(CrmScoreKind, native_enum=False, length=32),
        default=CrmScoreKind.CLIENT,
    )
    grade: Mapped[CrmScoreGrade] = mapped_column(
        Enum(CrmScoreGrade, native_enum=False, length=32),
        default=CrmScoreGrade.MOYEN,
    )
    computed_on: Mapped[datetime.date | None] = mapped_column(
        Date, default=None
    )
    season: Mapped[str] = mapped_column(String(40), default="")
    total_score: Mapped[int] = mapped_column(default=0)
    volume_score: Mapped[int] = mapped_column(default=0)
    frequency_score: Mapped[int] = mapped_column(default=0)
    seniority_score: Mapped[int] = mapped_column(default=0)
    punctuality_score: Mapped[int] = mapped_column(default=0)
    profitability_score: Mapped[int] = mapped_column(default=0)
    growth_score: Mapped[int] = mapped_column(default=0)
    quality_score: Mapped[int] = mapped_column(default=0)
    lead_time_score: Mapped[int] = mapped_column(default=0)
    reliability_score: Mapped[int] = mapped_column(default=0)
    average_payment_delay_days: Mapped[float] = mapped_column(
        Numeric(8, 2), default=0
    )
    turnover_amount: Mapped[float] = mapped_column(Numeric(16, 2), default=0)
    transaction_count: Mapped[int] = mapped_column(default=0)
    incident_count: Mapped[int] = mapped_column(default=0)
    comment: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), init=False
    )

    partner: Mapped["CrmPartner"] = relationship(
        back_populates="scores", init=False, repr=False
    )


class CrmAuditLog(Base):
    """Journal d'audit CRM : qui, quand, quoi, ancienne et nouvelle valeur."""

    __tablename__ = "crm_audit_log"

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    partner_id: Mapped[int | None] = mapped_column(
        ForeignKey("crm_partner.id", ondelete="SET NULL"), default=None
    )
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("app_user.id", ondelete="SET NULL"), default=None
    )
    actor_label: Mapped[str] = mapped_column(String(160), default="Système")
    action: Mapped[str] = mapped_column(String(40), default="consultation")
    entity_type: Mapped[str] = mapped_column(String(60), default="")
    entity_id: Mapped[int] = mapped_column(default=0)
    entity_ref: Mapped[str] = mapped_column(String(200), default="")
    field_name: Mapped[str] = mapped_column(String(120), default="")
    old_value: Mapped[str] = mapped_column(Text, default="")
    new_value: Mapped[str] = mapped_column(Text, default="")
    summary: Mapped[str] = mapped_column(Text, default="")
    module_route: Mapped[str] = mapped_column(String(160), default="/crm")
    ip_address: Mapped[str] = mapped_column(String(60), default="")
    is_sensitive: Mapped[bool] = mapped_column(default=False)
    occurred_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), default=None
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), init=False
    )
