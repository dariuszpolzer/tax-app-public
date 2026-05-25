import csv


def pln(x):
    return f"{x:.2f}".replace(".", ",")


def export_monthly_report(
    monthly_jpk,
    delegations_monthly,
    other_costs_monthly,
    pit_monthly,
    health_monthly,
    out_file,
):
    with open(out_file, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f, delimiter=";")

        writer.writerow(
            [
                "Miesiąc",
                "Sprzedaż netto",
                "Koszty netto",
                "VAT należny",
                "VAT naliczony",
                "VAT do zapłaty",
                "Delegacje",
                "Inne koszty",
                "Dochód JDG narastająco",
                "PIT JDG narastająco",
                "Zaliczka PIT JDG",
                "Dochód JDG do zdrowotnej",
                "Składka zdrowotna JDG",
            ]
        )

        for month in sorted(monthly_jpk.keys()):
            jpk = monthly_jpk[month]
            pit = pit_monthly.get(month, {})
            health = health_monthly.get(month)

            writer.writerow(
                [
                    month,
                    pln(jpk["sales_net"]),
                    pln(jpk["purchase_net"]),
                    pln(jpk["sales_vat"]),
                    pln(jpk["purchase_vat"]),
                    pln(jpk["sales_vat"] - jpk["purchase_vat"]),
                    pln(delegations_monthly.get(month, 0)),
                    pln(other_costs_monthly.get(month, 0)),
                    pln(pit.get("income_cumulative", 0)),
                    pln(pit.get("pit_cumulative", 0)),
                    pln(pit.get("pit_payment", 0)),
                    pln(health.business_income if health else 0),
                    pln(health.contribution if health else 0),
                ]
            )


def export_yearly_report(
    year,
    trips_count,
    delegation_costs,
    other_costs_total,
    pension_income,
    spouse_income,
    individual_pit,
    joint_pit,
    joint_tax_saving,
    health_contribution_total,
    yearly_jpk,
    pit_result,
    out_file,
):
    with open(out_file, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f, delimiter=";")

        writer.writerow(["Rok", year])
        writer.writerow(["Delegacje", trips_count])
        writer.writerow(["Koszty delegacji", pln(delegation_costs)])
        writer.writerow(["Inne koszty", pln(other_costs_total)])
        writer.writerow(["Emerytura", pln(pension_income)])
        writer.writerow(["Dochód małżonka", pln(spouse_income)])
        writer.writerow([])

        # writer.writerow(["Sprzedaż netto", round(yearly_jpk["sales_net"], 2)])
        # writer.writerow(["Koszty netto", round(yearly_jpk["purchase_net"], 2)])

        # writer.writerow([])

        # writer.writerow(["Podstawa PIT", round(pit_result.taxable_income, 2)])
        # writer.writerow(["PIT", round(pit_result.tax, 2)])

        # writer.writerow([])

        # writer.writerow(["VAT należny", round(yearly_jpk["sales_vat"], 2)])
        # writer.writerow(["VAT naliczony", round(yearly_jpk["purchase_vat"], 2)])
        # writer.writerow(["VAT do zapłaty", round(yearly_jpk["vat_to_pay"], 2)])

        writer.writerow(["Sprzedaż netto", pln(yearly_jpk["sales_net"])])
        writer.writerow(["Koszty netto", pln(yearly_jpk["purchase_net"])])
        writer.writerow([])
        writer.writerow(["Podstawa PIT", pln(pit_result.taxable_income)])
        writer.writerow(["PIT", pln(pit_result.tax)])
        writer.writerow(["Składka zdrowotna JDG", pln(health_contribution_total)])
        writer.writerow(["PIT osobno", pln(individual_pit.tax)])
        if joint_pit is not None:
            writer.writerow(["PIT wspólnie", pln(joint_pit.tax)])
            writer.writerow(["Różnica wspólnie vs osobno", pln(joint_tax_saving)])
        writer.writerow([])
        writer.writerow(["VAT należny", pln(yearly_jpk["sales_vat"])])
        writer.writerow(["VAT naliczony", pln(yearly_jpk["purchase_vat"])])
        writer.writerow(["VAT do zapłaty", pln(yearly_jpk["vat_to_pay"])])
