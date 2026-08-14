from app.services.scenario_service import ScenarioService


def test_department_reduction_calculation_is_transparent() -> None:
    calculation = ScenarioService.calculate(
        baseline_projected_cost=1000.0,
        department_cost_share_pct=25.0,
        reduction_pct=10.0,
    )

    assert calculation == {
        "department_cost_share_pct": 25.0,
        "reduction_pct": 10.0,
        "baseline_projected_cost": 1000.0,
        "estimated_reduction_amount": 25.0,
        "scenario_projected_cost": 975.0,
        "impact_pct": 2.5,
    }
