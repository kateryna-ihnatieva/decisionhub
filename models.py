from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.postgresql import JSON

db = SQLAlchemy()


# --- HIERARCHY ---


class HierarchyCriteria(db.Model):
    __tablename__ = "hierarchy_criteria"
    id = db.Column(db.Integer, primary_key=True)
    names = db.Column(JSON, nullable=False)


class HierarchyAlternatives(db.Model):
    __tablename__ = "hierarchy_alternatives"
    id = db.Column(db.Integer, primary_key=True)
    names = db.Column(JSON, nullable=False)


class HierarchyTask(db.Model):
    __tablename__ = "hierarchy_tasks"
    id = db.Column(db.Integer, primary_key=True)
    task = db.Column(db.Text)


class HierarchyCriteriaMatrix(db.Model):
    __tablename__ = "hierarchy_criteria_matrix"
    id = db.Column(db.Integer, primary_key=True)
    hierarchy_criteria_id = db.Column(
        db.Integer, db.ForeignKey("hierarchy_criteria.id"), nullable=False
    )
    comparison_matrix = db.Column(JSON, nullable=False)
    components_eigenvector = db.Column(JSON, nullable=False)
    normalized_eigenvector = db.Column(JSON, nullable=False)
    sum_col = db.Column(JSON, nullable=False)
    prod_col = db.Column(JSON, nullable=False)
    l_max = db.Column(JSON, nullable=False)
    index_consistency = db.Column(JSON, nullable=False)
    relation_consistency = db.Column(JSON, nullable=False)
    lst_normalized_eigenvector = db.Column(JSON, nullable=False)
    ranj = db.Column(JSON, nullable=False)


class HierarchyAlternativesMatrix(db.Model):
    __tablename__ = "hierarchy_alternatives_matrix"
    id = db.Column(db.Integer, primary_key=True)
    criteria_id = db.Column(
        db.Integer, db.ForeignKey("hierarchy_criteria.id"), nullable=False
    )
    hierarchy_alternatives_id = db.Column(
        db.Integer, db.ForeignKey("hierarchy_alternatives.id"), nullable=False
    )
    matr_alt = db.Column(JSON, nullable=False)
    comparison_matrix = db.Column(JSON, nullable=False)
    components_eigenvector_alt = db.Column(JSON, nullable=False)
    normalized_eigenvector_alt = db.Column(JSON, nullable=False)
    sum_col_alt = db.Column(JSON, nullable=False)
    prod_col_alt = db.Column(JSON, nullable=False)
    l_max_alt = db.Column(JSON, nullable=False)
    index_consistency_alt = db.Column(JSON, nullable=False)
    relation_consistency_alt = db.Column(JSON, nullable=False)
    lst_normalized_eigenvector_alt = db.Column(JSON, nullable=False)
    ranj_alt = db.Column(JSON, nullable=False)
    global_prior = db.Column(JSON, nullable=False)
    lst_normalized_eigenvector_global = db.Column(JSON, nullable=False)
    ranj_global = db.Column(JSON, nullable=False)
    global_priorities_plot_id = db.Column(
        db.Integer, db.ForeignKey("global_priorities_plot.id"), nullable=False
    )
    task_id = db.Column(db.Integer, db.ForeignKey("hierarchy_tasks.id"), nullable=True)
    gpt_response = db.Column(db.Text)


class GlobalPrioritiesPlot(db.Model):
    __tablename__ = "global_priorities_plot"
    id = db.Column(db.Integer, primary_key=True)
    plot_data = db.Column(JSON, nullable=False)


# --- LAPLASA ---


class LaplasaConditions(db.Model):
    __tablename__ = "laplasa_conditions"
    id = db.Column(db.Integer, primary_key=True)
    names = db.Column(JSON, nullable=False)


class LaplasaAlternatives(db.Model):
    __tablename__ = "laplasa_alternatives"
    id = db.Column(db.Integer, primary_key=True)
    names = db.Column(JSON, nullable=False)


class LaplasaTask(db.Model):
    __tablename__ = "laplasa_tasks"
    id = db.Column(db.Integer, primary_key=True)
    task = db.Column(db.Text)


class LaplasaCostMatrix(db.Model):
    __tablename__ = "laplasa_cost_matrix"
    id = db.Column(db.Integer, primary_key=True)
    laplasa_alternatives_id = db.Column(
        db.Integer, db.ForeignKey("laplasa_alternatives.id"), nullable=False
    )
    matrix = db.Column(JSON, nullable=False)
    optimal_variants = db.Column(JSON, nullable=False)
    task_id = db.Column(db.Integer, db.ForeignKey("laplasa_tasks.id"), nullable=True)


# --- MAXIMIN ---


class MaximinConditions(db.Model):
    __tablename__ = "maximin_conditions"
    id = db.Column(db.Integer, primary_key=True)
    names = db.Column(JSON, nullable=False)


class MaximinAlternatives(db.Model):
    __tablename__ = "maximin_alternatives"
    id = db.Column(db.Integer, primary_key=True)
    names = db.Column(JSON, nullable=False)


class MaximinTask(db.Model):
    __tablename__ = "maximin_tasks"
    id = db.Column(db.Integer, primary_key=True)
    task = db.Column(db.Text, nullable=False, default="")
    matrix_type = db.Column(db.String(20), nullable=False, default="profit")


class MaximinCostMatrix(db.Model):
    __tablename__ = "maximin_cost_matrix"
    id = db.Column(db.Integer, primary_key=True)
    maximin_alternatives_id = db.Column(
        db.Integer, db.ForeignKey("maximin_alternatives.id"), nullable=False
    )
    matrix = db.Column(JSON, nullable=False)
    optimal_variants = db.Column(JSON, nullable=False)
    task_id = db.Column(db.Integer, db.ForeignKey("maximin_tasks.id"), nullable=True)


# --- SAVAGE ---


class SavageConditions(db.Model):
    __tablename__ = "savage_conditions"
    id = db.Column(db.Integer, primary_key=True)
    names = db.Column(JSON, nullable=False)


class SavageAlternatives(db.Model):
    __tablename__ = "savage_alternatives"
    id = db.Column(db.Integer, primary_key=True)
    names = db.Column(JSON, nullable=False)


class SavageTask(db.Model):
    __tablename__ = "savage_tasks"
    id = db.Column(db.Integer, primary_key=True)
    task = db.Column(db.Text)


class SavageCostMatrix(db.Model):
    __tablename__ = "savage_cost_matrix"
    id = db.Column(db.Integer, primary_key=True)
    savage_alternatives_id = db.Column(
        db.Integer, db.ForeignKey("savage_alternatives.id"), nullable=False
    )
    matrix = db.Column(JSON, nullable=False)
    loss_matrix = db.Column(JSON, nullable=False)
    max_losses = db.Column(JSON, nullable=False)
    optimal_variants = db.Column(JSON, nullable=False)
    task_id = db.Column(db.Integer, db.ForeignKey("savage_tasks.id"), nullable=True)


# --- HURWITZ ---


class HurwitzConditions(db.Model):
    __tablename__ = "hurwitz_conditions"
    id = db.Column(db.Integer, primary_key=True)
    names = db.Column(JSON, nullable=False)


class HurwitzAlternatives(db.Model):
    __tablename__ = "hurwitz_alternatives"
    id = db.Column(db.Integer, primary_key=True)
    names = db.Column(JSON, nullable=False)


class HurwitzTask(db.Model):
    __tablename__ = "hurwitz_tasks"
    id = db.Column(db.Integer, primary_key=True)
    task = db.Column(db.Text)


class HurwitzCostMatrix(db.Model):
    __tablename__ = "hurwitz_cost_matrix"
    id = db.Column(db.Integer, primary_key=True)
    hurwitz_alternatives_id = db.Column(
        db.Integer, db.ForeignKey("hurwitz_alternatives.id"), nullable=False
    )
    matrix = db.Column(JSON, nullable=False)
    optimal_variants = db.Column(JSON, nullable=False)
    alpha = db.Column(db.Float, nullable=False)
    task_id = db.Column(db.Integer, db.ForeignKey("hurwitz_tasks.id"), nullable=True)


# --- BINARY ---


class BinaryNames(db.Model):
    __tablename__ = "binary_names"
    id = db.Column(db.Integer, primary_key=True)
    names = db.Column(JSON, nullable=False)


class BinaryTask(db.Model):
    __tablename__ = "binary_tasks"
    id = db.Column(db.Integer, primary_key=True)
    task = db.Column(db.Text)


class BinaryMatrix(db.Model):
    __tablename__ = "binary_matrix"
    id = db.Column(db.Integer, primary_key=True)
    binary_names_id = db.Column(
        db.Integer, db.ForeignKey("binary_names.id"), nullable=False
    )
    matrix = db.Column(JSON, nullable=False)


class BinaryRanj(db.Model):
    __tablename__ = "binary_ranj"
    id = db.Column(db.Integer, primary_key=True)
    binary_names_id = db.Column(
        db.Integer, db.ForeignKey("binary_names.id"), nullable=False
    )
    binary_matrix_id = db.Column(
        db.Integer, db.ForeignKey("binary_matrix.id"), nullable=False
    )
    sorted_sum = db.Column(JSON, nullable=False)
    ranj = db.Column(db.String(255), nullable=False)
    plot_data = db.Column(JSON, nullable=False)


class BinaryTransitivity(db.Model):
    __tablename__ = "binary_transitivity"
    id = db.Column(db.Integer, primary_key=True)
    binary_names_id = db.Column(
        db.Integer, db.ForeignKey("binary_names.id"), nullable=False
    )
    binary_matrix_id = db.Column(
        db.Integer, db.ForeignKey("binary_matrix.id"), nullable=False
    )
    binary_ranj_id = db.Column(
        db.Integer, db.ForeignKey("binary_ranj.id"), nullable=False
    )
    comb = db.Column(JSON, nullable=False)
    condition_transitivity = db.Column(JSON, nullable=False)
    ratio = db.Column(JSON, nullable=False)
    note = db.Column(JSON, nullable=False)
    binary_conclusion = db.Column(JSON, nullable=False)
    task_id = db.Column(db.Integer, db.ForeignKey("binary_tasks.id"), nullable=True)


# --- EXPERTS ---
class ExpertsNameResearch(db.Model):
    __tablename__ = "experts_name_research"
    id = db.Column(db.Integer, primary_key=True)
    names = db.Column(JSON, nullable=False)


class ExpertsTask(db.Model):
    __tablename__ = "experts_tasks"
    id = db.Column(db.Integer, primary_key=True)
    task = db.Column(db.Text)


class ExpertsCompetency(db.Model):
    __tablename__ = "experts_competency"
    id = db.Column(db.Integer, primary_key=True)
    table_competency = db.Column(JSON, nullable=False)
    k_k = db.Column(JSON, nullable=False)
    k_a = db.Column(JSON, nullable=False)


class ExpertsData(db.Model):
    __tablename__ = "experts_data"
    id = db.Column(db.Integer, primary_key=True)
    experts_name_research_id = db.Column(
        db.Integer, db.ForeignKey("experts_name_research.id"), nullable=False
    )
    experts_data_table = db.Column(JSON, nullable=False)
    m_i = db.Column(JSON, nullable=False)
    r_i = db.Column(JSON, nullable=False)
    lambda_value = db.Column(JSON, nullable=False)


# --- USERS ---
class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    psw = db.Column(db.String(255), nullable=False)


# --- RESULTS ---
class Result(db.Model):
    __tablename__ = "results"
    id = db.Column(db.Integer, primary_key=True)
    method_name = db.Column(db.String(255), nullable=False)
    method_id = db.Column(db.Integer, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
