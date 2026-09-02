# -*- coding: utf-8 -*-
import processing
from qgis.core import (QgsVectorLayer, QgsFeature, QgsGeometry, QgsField, QgsPointXY,
                       QgsFields, QgsProject, QgsVectorFileWriter, QgsWkbTypes, QgsRasterLayer,
                       QgsCoordinateTransform)
from qgis.PyQt.QtCore import QVariant
import math
import os
import csv

# --- PERBAIKAN MATEMATIS PADA RUMUS ALOMETRIK ---
# Catatan: Semua persamaan yang mengandung log atau ln telah diubah menjadi
# bentuk eksponensial (antilog) math.exp() untuk ln, dan 10**() untuk log10.
# Persamaan pangkat biasa (D**x) dan linier tetap sama.

NON_MANGROVE_EQ = {
    'borassodendron borneensis': (None, None, lambda D: 0.0123 * (D**2)),
    'musa sp.': (7, 27, lambda D: 0.030 * (D**2.13)),
    'dipterocarpus sp.': (5, 70, lambda D: math.exp(-1.232 + 2.178 * math.log(D))), # Dikoreksi: exp()
    'hevea brasiliensis': (26.1, 36.8, lambda D: 419 - 16.9*D + 0.322*(D**2)),
    'hopea sp.': (5, 70, lambda D: math.exp(-1.813 + 2.339 * math.log(D))), # Dikoreksi: exp()
    'gigantochloa sp.': (3, 7, lambda D: 0.131 * (D**2.278)),
    'intsia sp.': (5.5, 40, lambda D: 10**(-0.762 + 2.51 * math.log10(D))), # Dikoreksi: 10**()
    'palaquium sp.': (5, 70, lambda D: math.exp(-1.098 + 2.142 * math.log(D))), # Dikoreksi: exp()
    'elaeis guineensis': (None, None, lambda D: 0.0002 * (D**3.49)),
    'coffea sp.': (1, 10, lambda D: 0.2822 * (D**2.0636)),
    'pometia sp.': (5, 40, lambda D: 10**(-0.8406 + 2.572 * math.log10(D))), # Dikoreksi: 10**()
    'tectona grandis': (4.8, 26.2, lambda D: 0.054 * (D**2.579)),
    'shorea sp.': (5, 70, lambda D: math.exp(-2.193 + 2.371 * math.log(D))), # Dikoreksi: exp()
    'swietenia macrophylla': (14.3, 36.9, lambda D: 10**(1.32 + 2.65 * math.log10(D))), # Dikoreksi: 10**()
    'shorea parvifolia': (5, 40, lambda D: 0.09 * (D**2.58)),
    'ficus sp.': (3.5, 9.1, lambda D: math.exp(-2.59 + 2.6 * math.log(D))), # Dikoreksi: exp()
    'geunsia pentandra': (3.4, 16.2, lambda D: math.exp(-2.89 + 2.62 * math.log(D))), # Dikoreksi: exp()
    'piper aduncum': (3.2, 8.3, lambda D: math.exp(-2.42 + 2.39 * math.log(D))), # Dikoreksi: exp()
    'gonystylus bancanus': (10, 75.1, lambda D: math.exp(-2.47 + 2.44 * math.log(D))), # Dikoreksi: exp()
    'schima wallichii': (3, 24.6, lambda D: 0.459 * (D**1.366)),
    'dipterocarpus kerrii': (5, 40, lambda D: 0.217 * (D**2.38)),
    'cotylelobium burckii': (5, 40, lambda D: 0.30 * (D**2.29)),
    'pinus merkusii': (4, 44, lambda D: 0.094 * (D**2.432)),
    'paraserianthes falcataria': (None, 43.8, lambda D: 10**(-1.239 + 2.561 * math.log10(D))), # Dikoreksi: 10**()
    'elmerrillia celebica': (6.9, 37.2, lambda D: 10**(-0.701 + 2.4 * math.log10(D))), # Dikoreksi: 10**()
    'elmerrillia ovalis': (7.5, 50, lambda D: 10**(-1.190 + 2.71 * math.log10(D))), # Dikoreksi: 10**()
    'acacia crassicarpa': (6, 28, lambda D: 0.0267 * (D**2.8912)),
    'acacia mangium': (1.4, 18.9, lambda D: 0.1997 * (D**2.2351)),
    'agathis loranthifolia': (1, 10, lambda D: 0.001 * (D**4.195)),
    'eucalyptus grandis': (2.4, 27.2, lambda D: 0.0678 * (D**2.5794))
}

NON_MANGROVE_GENUS = {
    'dipterocarpus': NON_MANGROVE_EQ['dipterocarpus sp.'],
    'hopea': NON_MANGROVE_EQ['hopea sp.'],
    'gigantochloa': NON_MANGROVE_EQ['gigantochloa sp.'],
    'intsia': NON_MANGROVE_EQ['intsia sp.'],
    'palaquium': NON_MANGROVE_EQ['palaquium sp.'],
    'coffea': NON_MANGROVE_EQ['coffea sp.'],
    'pometia': NON_MANGROVE_EQ['pometia sp.'],
    'shorea': NON_MANGROVE_EQ['shorea sp.'],
    'ficus': NON_MANGROVE_EQ['ficus sp.'],
    'musa': NON_MANGROVE_EQ['musa sp.']
}

MANGROVE_EQ = {
    'xylocarpus granatum': lambda D: 10**(-0.763 + 2.23 * math.log10(D)), # Dikoreksi: 10**()
    'rhizophora mucronata': lambda D: 0.5 * (D**2.32),
    'rhizophora apiculata': lambda D: 0.75 * (D**2.23),
    'bruguiera gymnorrhiza': lambda D: -0.552 + 2.244 * D, # Persamaan linier, tetap sama
    'avicennia marina': lambda D: 0.291 * (D**2.260),
    'ceriop tagal': lambda D: 0.251 * 0.97 * (D**2.46),
    'heritiera littoralis': lambda D: 0.251 * (D**2.46),
    'sonneratia alba': lambda D: 0.251 * 0.78 * (D**2.46),
    'sonneratia caseolaris': lambda D: 0.251 * 0.5 * (D**2.46),
    'aegiceras corniculata': lambda D: 0.251 * 0.64 * (D**2.46),
    'xylocarpus moluccensis': lambda D: 0.251 * 0.74 * (D**2.46)
}

MANGROVE_GENUS = {
    'bruguiera': lambda D: 10.11 * (D**1.3),
    'rhizophora': lambda D: 0.235 * (D**2.42),
    'avicennia': lambda D: 0.308 * (D**2.11)
}

EQ_POHON_LAIN = lambda D: 0.1728 * (D**2.2234)
EQ_PALMAE = lambda D: math.exp(-2.134 + 2.530 * math.log(D)) # Sudah benar (sudah pakai exp)

def get_biomass(species, genus, dbh, is_mangrove):
    sp_key = str(species).lower().strip() if species else ""
    gen_key = str(genus).lower().strip() if genus else ""

    if sp_key == 'palmae' or gen_key == 'palmae':
        return EQ_PALMAE(dbh)

    if is_mangrove:
        if sp_key in MANGROVE_EQ: return MANGROVE_EQ[sp_key](dbh)
        if gen_key in MANGROVE_GENUS: return MANGROVE_GENUS[gen_key](dbh)
        return EQ_POHON_LAIN(dbh)
    else:
        eq = NON_MANGROVE_EQ.get(sp_key) or NON_MANGROVE_GENUS.get(gen_key)
        if eq:
            min_d, max_d, func = eq
            if (min_d and dbh < min_d) or (max_d and dbh > max_d):
                return EQ_POHON_LAIN(dbh)
            return func(dbh)
        return EQ_POHON_LAIN(dbh)

def run_carbon_estimation(layer, plot_fld, sp_fld, gen_fld, dbh_fld, is_mangrove, aoi_layer, pixel_size, out_dir):
    crs = layer.crs()
    
    if crs.isGeographic() and pixel_size > 1:
        raise ValueError("Layer menggunakan koordinat Geografis (WGS84/Derajat). "
                         "Ubah layer ke UTM (Projected) terlebih dahulu atau sesuaikan ukuran pixel (misal 0.0001).")

    out_shp = os.path.join(out_dir, "Titik_Cadangan_Karbon.shp")
    out_csv = os.path.join(out_dir, "Tabel_Hasil_Karbon.csv")

    fields = QgsFields()
    fields.append(QgsField("Plot_ID", QVariant.String))
    fields.append(QgsField("Spesies", QVariant.String))
    fields.append(QgsField("DBH", QVariant.Double))
    fields.append(QgsField("Biomassa", QVariant.Double))
    fields.append(QgsField("Karbon_kg", QVariant.Double))
    fields.append(QgsField("C_ha_Mg", QVariant.Double))
    fields.append(QgsField("CO2_ton_ha", QVariant.Double))

    writer = QgsVectorFileWriter(out_shp, "UTF-8", fields, QgsWkbTypes.Point, crs, "ESRI Shapefile")
    plot_stats = {}

    with open(out_csv, 'w', newline='', encoding='utf-8') as csvfile:
        csvwriter = csv.writer(csvfile)
        csvwriter.writerow(['Plot_ID', 'Spesies', 'Genus', 'DBH_cm', 'Biomassa_kg', 'Karbon_kg', 'C_Mg_ha', 'CO2_ton_ha'])

        for feat in layer.getFeatures():
            dbh_raw = feat[dbh_fld]
            if isinstance(dbh_raw, str): dbh_raw = dbh_raw.replace(',', '.')
            try: dbh = float(dbh_raw)
            except: continue

            sp = feat[sp_fld]
            gen = feat[gen_fld]
            plot_id = str(feat[plot_fld])

            B = get_biomass(sp, gen, dbh, is_mangrove)
            C = B * 0.47

            l_plot = 0
            if is_mangrove:
                if dbh > 10: l_plot = 100
                elif 2 <= dbh <= 10: l_plot = 25
                elif dbh < 2: l_plot = 4
            else:
                if dbh >= 20: l_plot = 400
                elif 10 <= dbh < 20: l_plot = 100
                elif 5 <= dbh < 10: l_plot = 25
                
            C_ha = (C / 1000) * (10000 / l_plot) if l_plot > 0 else 0
            CO2_ha = C_ha * 3.67

            out_feat = QgsFeature()
            out_feat.setGeometry(feat.geometry())
            out_feat.setAttributes([plot_id, sp, dbh, B, C, C_ha, CO2_ha])
            writer.addFeature(out_feat)
            
            csvwriter.writerow([plot_id, sp, gen, dbh, round(B,4), round(C,4), round(C_ha,4), round(CO2_ha,4)])

            geom = feat.geometry()
            if geom is None or geom.isEmpty():
                continue
            pt = geom.asMultiPoint()[0] if geom.isMultipart() else geom.asPoint()
            
            if plot_id not in plot_stats:
                plot_stats[plot_id] = {'x': pt.x(), 'y': pt.y(), 'C_ha': 0, 'CO2_ha': 0}
            plot_stats[plot_id]['C_ha'] += C_ha
            plot_stats[plot_id]['CO2_ha'] += CO2_ha

    del writer
    QgsProject.instance().addMapLayer(QgsVectorLayer(out_shp, "Hasil Poin Karbon", "ogr"))

    if not plot_stats:
        raise ValueError("Tidak ada data plot yang valid untuk diinterpolasi.")

    centroid_shp = os.path.join(out_dir, "Plot_Centroids.shp")
    c_fields = QgsFields()
    c_fields.append(QgsField("Plot_ID", QVariant.String))
    c_fields.append(QgsField("Tot_C_ha", QVariant.Double))
    c_fields.append(QgsField("Tot_CO2_ha", QVariant.Double))
    
    c_writer = QgsVectorFileWriter(centroid_shp, "UTF-8", c_fields, QgsWkbTypes.Point, crs, "ESRI Shapefile")
    for pid, st in plot_stats.items():
        f = QgsFeature()
        f.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(st['x'], st['y'])))
        f.setAttributes([pid, st['C_ha'], st['CO2_ha']])
        c_writer.addFeature(f)
    del c_writer

    centroid_layer = QgsVectorLayer(centroid_shp, "Centroid Plot Karbon", "ogr")
    if not centroid_layer.isValid():
        raise RuntimeError(f"Gagal memuat shapefile centroid: {centroid_shp}")
    QgsProject.instance().addMapLayer(centroid_layer)

    idx_c = centroid_layer.fields().indexOf("Tot_C_ha")
    idx_co2 = centroid_layer.fields().indexOf("Tot_CO2_ha")
    
    if idx_c == -1 or idx_co2 == -1:
        raise RuntimeError("Kolom Z tidak ditemukan di shapefile centroid!")

    if aoi_layer:
        aoi_crs = aoi_layer.crs()
        if aoi_crs != crs:
            xform = QgsCoordinateTransform(aoi_crs, crs, QgsProject.instance())
            target_extent = xform.transformBoundingBox(aoi_layer.extent())
        else:
            target_extent = aoi_layer.extent()
    else:
        target_extent = centroid_layer.extent()
        
    if target_extent.isEmpty() or target_extent.width() < pixel_size or target_extent.height() < pixel_size:
        target_extent.grow(pixel_size * 2)

    ext_str = f"{target_extent.xMinimum()},{target_extent.xMaximum()},{target_extent.yMinimum()},{target_extent.yMaximum()}"

    raster_c = os.path.join(out_dir, "IDW_Cadangan_Karbon.tif").replace('\\', '/')
    processing.run("qgis:idwinterpolation", {
        'INTERPOLATION_DATA': f"{centroid_layer.id()}::~::0::~::{idx_c}::~::0",
        'DISTANCE_COEFFICIENT': 2,
        'EXTENT': ext_str,
        'PIXEL_SIZE': pixel_size,
        'OUTPUT': raster_c
    })
    QgsProject.instance().addMapLayer(QgsRasterLayer(raster_c, "IDW Cadangan Karbon (Mg/ha)"))

    raster_co2 = os.path.join(out_dir, "IDW_Serapan_CO2.tif").replace('\\', '/')
    processing.run("qgis:idwinterpolation", {
        'INTERPOLATION_DATA': f"{centroid_layer.id()}::~::0::~::{idx_co2}::~::0",
        'DISTANCE_COEFFICIENT': 2,
        'EXTENT': ext_str,
        'PIXEL_SIZE': pixel_size,
        'OUTPUT': raster_co2
    })
    QgsProject.instance().addMapLayer(QgsRasterLayer(raster_co2, "IDW Serapan CO2 (Ton/ha)"))