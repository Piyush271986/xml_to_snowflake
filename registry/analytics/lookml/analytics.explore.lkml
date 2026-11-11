include: "/views/*.view.lkml"

explore: assets {
  label: "Analytics Reference Model"
  description: "Golden curated layer for analytics securities data"

  join: asset {
    type: left_outer
    relationship: one_to_many
    sql_on: ${TABLE}.assets_pk = ${asset}.assets_fk ;;
  }

  join: country_classification {
    type: left_outer
    relationship: one_to_many
    sql_on: ${asset}.asset_pk = ${country_classification}.asset_fk ;;
  }

  join: cusip2 {
    type: left_outer
    relationship: one_to_many
    sql_on: ${asset}.asset_pk = ${cusip2}.asset_fk ;;
  }

  join: cusip_alias {
    type: left_outer
    relationship: one_to_many
    sql_on: ${asset}.asset_pk = ${cusip_alias}.asset_fk ;;
  }

}
