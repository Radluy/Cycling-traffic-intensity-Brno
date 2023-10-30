var portal = Portal("https://www.arcgis.com");

var layer = FeatureSetByPortalItem(portal, "de067cdb24b9449894dac94d05663305", 0, ["*"], false);
var iter = 1;

var features = [];
var new_feat;
//2 types of formats: "dd.mm.yyyy hh:mm", "yyyy/mm/dd hh:mm:ss"
for (var feat in layer) {
  var date1 = Split(feat['datum'], ' ');
  var time = Split(date1[1], ':')[0];
  //Console(Find(feat['datum'], '/'))
  if (Find('/', feat['datum']) != -1) {
    var date2 = Split(date1[0], '/');
    var final_date = Date(date2[0], date2[1], date2[2], time);
  } else {
    var date2 = Split(date1[0], '.');
    var final_date = Date(date2[2], date2[1], date2[0], time);
  }
  
  new_feat = Feature(feat);
  new_feat['datum'] = final_date;
  Push(features, new_feat);

  /*iter += 1;
  if (iter > 10000000){
    break;
  }*/
}

var fields = Schema(features[0]).fields;

var new_fields = [];
for (var index in fields) {
  if (fields[index]["name"] == "datum"){
    var datefield = {"alias":"datum","name":"datum", "type":"esriFieldTypeDate"};
    Push(new_fields, datefield);
  } else {
    Push(new_fields, fields[index]);
  }
}

var out_dict = { 
    'fields': new_fields,
    'geometryType': '', 
    'features': features 
}; 

return FeatureSet(out_dict); 
//return layer;

