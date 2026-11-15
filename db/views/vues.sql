-- Vue instantannée
CREATE OR REPLACE VIEW view_positions_actuelles as
SELECT 
    mvt.pdt_id, 
    pdt.pdt_nom_produit,
    -- La somme de toutes les parts (Achats + Ventes en négatif)
    SUM(mvt.mvt_nb_parts) as quantite_detenue,
    pdt.ptf_id,
    pdt.pdt_cash,
    pdt.pdt_est_actif,
    ptf.ptf_type_enveloppe
FROM public.mouvement_mvt mvt
INNER JOIN public.produit_financier_pdt pdt ON pdt.pdt_id = mvt.pdt_id
INNER JOIN public.portefeuille_ptf ptf ON ptf.ptf_id = pdt.ptf_id
GROUP BY mvt.pdt_id, pdt.pdt_nom_produit, pdt.pdt_cash, pdt.ptf_id, pdt.pdt_est_actif, ptf.ptf_type_enveloppe;

-- Vue PRU
CREATE OR REPLACE VIEW view_pru AS
SELECT 
    pdt_id,
    -- On garde la logique de calcul avec les frais
    CASE 
        WHEN SUM(CASE WHEN mvt_nb_parts > 0 THEN mvt_nb_parts ELSE 0 END) > 0 
        THEN SUM(CASE WHEN mvt_nb_parts > 0 THEN (mvt_nb_parts * mvt_prix) + mvt_frais ELSE 0 END) 
            / SUM(CASE WHEN mvt_nb_parts > 0 THEN mvt_nb_parts ELSE 0 END)
        ELSE 0 
    END as pru
FROM public.mouvement_mvt
GROUP BY pdt_id;
