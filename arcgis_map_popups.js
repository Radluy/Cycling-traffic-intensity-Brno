// Popup definitions in the ARCADE language of ArcGIS

// BikeToWork segment
var biketowork_id = $feature.biketowork_id //feature clicked in reference model
var biketowork_set = FeatureSetById($map, "186eb71977e-layer-48") // id of MMB layer found in ArcGIS portal
var biketowork_data = First(Filter(biketowork_set, 'GID_ROAD = @biketowork_id')) 

return {
    type: 'fields',
    title: 'Bike To Work campaign',
    fieldInfos:  [{
          fieldName: "GID_ROAD"  
        },
        {
          fieldName: "Cyclists-May-2018" 
        },
        {
          fieldName: "Cyclists-May-2020"  
        },
        {
          fieldName: "Cyclists-May-2021"  
        },
        {
          fieldName: "Cyclists-May-2022"  
        }],
    attributes : {"GID_ROAD" : biketowork_data.GID_ROAD, 
                 "Cyclists-May-2018" : biketowork_data.data_2018, 
                 "Cyclists-May-2019" : biketowork_data.data_2019,
                 "Cyclists-May-2020" : biketowork_data.data_2020,
                 "Cyclists-May-2021" : biketowork_data.data_2021,
                 "Cyclists-May-2022" : biketowork_data.dpnk_22,}  
  }

// City Census segment (BKOM)
var census_id = $feature.city_census_id //feature clicked in reference model 
var census_set = FeatureSetById($map, "186f8edce24-layer-5") // id of MMB layer found in ArcGIS portal
var census_data = First(Filter(census_set, 'id = @census_id'))

return {
    type: 'fields',
    title: 'City cycling traffic census (BKOM)',
    fieldInfos:  [{
          fieldName: "id"  
        },
        {
          fieldName: "Cyclists-weekday-2016" 
        },
        {
          fieldName: "Cyclists-weekend-2016"  
        },
        {
          fieldName: "Cyclists-weekday-2018"  
        },
        {
          fieldName: "Cyclists-weekend-2018"  
        },
        {
          fieldName: "Cyclists-weekday-2020"  
        },
        {
          fieldName: "Cyclists-weekend-2020"  
        }],
    attributes : {"id" : census_data.id, 
                 "Cyclists-weekday-2016" : census_data.prac_2016, 
                 "Cyclists-weekend-2016" : census_data.vik_2016,
                 "Cyclists-weekday-2018" : census_data.prac_2018,
                 "Cyclists-weekend-2018" : census_data.vik_2018,
                 "Cyclists-weekday-2020" : census_data.prac_2020,
                 "Cyclists-weekend-2020" : census_data.vik_2020}  
  }

// Automatic counters segment -> multiple records for one location -> 
// can't display all data -> aggregation limited in the language
var counters_id = feature.counter_id
var counters_set = FeatureSetById($map, "186eb730d93-layer-49")
var counters_data = Filter(counters_set, 'LocationId = @counters_id')

var x = First(counters_data)
// not really daily group -> multiple records per day on semi-hour basis
var grouped_first = GroupBy(counters_data, "LocationId", {name:"avg_cyclists_first_direction", expression: "FirstDirection_Cyclists", statistic:'AVG'})
grouped_first = First(grouped_first)
var grouped_second = GroupBy(counters_data, "LocationId", {name:"avg_cyclists_second_direction", expression: "SecondDirection_Cyclists", statistic:'AVG'})
grouped_second = First(grouped_second)

return {
    type: 'fields',
    title: 'Automatic bike counters',
    fieldInfos:  [{
          fieldName: "LocationId",
        },
        {
          fieldName: "Street Name"
        },
        {
          fieldName: "Daily-Average-First-Direction"  
        },
        {
          fieldName: "Daily-Average-Second-Direction"  
        }],
    attributes : {"LocationId" : x.LocationId, 
                  "Street Name" : x.UnitName,
                  "Daily-Average-First-Direction" : grouped_first.avg_cyclists_first_direction,
                  "Daily-Average-Second-Direction" : grouped_second.avg_cyclists_second_direction}  
}

// ****************OPTION 2: grouping by specific day -> too slow****************
/*
// Convert datetime to date
var fs_date = {
    geometryType: "",
    fields: [
        {name: "DateShort", type: "esriFieldTypeDate"},
        {name: "FirstDirection_Cyclists", type: "esriFieldTypeIntege"},
        ],
    features: []
}
for(var f in counters_data) {
    var d = f.datum
    var date_short = Number(Date(Year(d), Month(d), Day(d)))
    Push(fs_date.features, {attributes: {DateShort: date_short, FirstDirection_Cyclists: f.FirstDirection_Cyclists}})
}

// group by and order by DateShort
var fs_grouped_by_date = GroupBy(FeatureSet(Text(fs_date)), "DateShort", {name: "Total", expression: "1", statistic: "COUNT"})
return fs_grouped_by_date
*/

