import streamlit as st
from supabase import create_client, Client

# Page configuration
st.set_page_config(page_title="Gestion des Membres", page_icon="👥", layout="wide")

# ---------------------------------------------------------
# GESTION DE LA CONNEXION (BARRIÈRE DE SÉCURITÉ)
# ---------------------------------------------------------
if "authentifie" not in st.session_state:
  st.session_state.authentifie = False

if not st.session_state.authentifie:
  st.title("🔒 Espace Restreint - Bureau de l'Association")
  st.info(
      "Cet espace est réservé aux membres du bureau. Veuillez entrer le mot de"
      " passe d'accès."
  )

  with st.form("form_connexion"):
    password_saisi = st.text_input(
        "Mot de passe administrateur", type="password"
    )
    submit_btn = st.form_submit_button("Se connecter")

    if submit_btn:
      if password_saisi == st.secrets.get("ADMIN_PASSWORD"):
        st.session_state.authentifie = True
        st.success("Connexion réussie !")
        st.rerun()
      else:
        st.error("Mot de passe incorrect.")

  # Stoppe l'exécution du reste du code si l'utilisateur n'est pas connecté
  st.stop()

# Connexion à Supabase via les secrets Streamlit
@st.cache_resource
def init_connection():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_connection()

st.title("👥 Gestion des Membres de l'Association")

# Menu latéral
menu = ["Consulter / Chercher", "Ajouter un membre", "Modifier / Supprimer"]
choice = st.sidebar.selectbox("Menu", menu)

# ---------------------------------------------------------
# 1. CONSULTATION DES MEMBRES
# ---------------------------------------------------------
if choice == "Consulter / Chercher":
    st.subheader("📋 Liste des Membres")
    
    # Récupération des données
    response = supabase.table("membres").select("*").execute()
    data = response.data
    
    if data:
        # Barre de recherche
        search = st.text_input("🔍 Rechercher par nom ou prénom")
        if search:
            data = [m for m in data if search.lower() in m['nom'].lower() or search.lower() in m['prenom'].lower()]
        
        # Affichage sous forme de tableau
        st.dataframe(data, use_container_width=True)
    else:
        st.info("Aucun membre trouvé dans la base.")

# ---------------------------------------------------------
# 2. AJOUT D'UN MEMBRE
# ---------------------------------------------------------
elif choice == "Ajouter un membre":
    st.subheader("➕ Ajouter une nouvelle fiche")
    
    with st.form("form_ajout", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            nom = st.text_input("Nom *")
            prenom = st.text_input("Prénom *")
            email = st.text_input("Email")
        with col2:
            telephone = st.text_input("Téléphone")
            statut = st.selectbox("Statut", ["Actif", "Inactif", "Bureau", "Honneur"])
            cotisation = st.checkbox("Cotisation à jour")
        
        submitted = st.form_submit_button("Enregistrer")
        
        if submitted:
            if nom and prenom:
                nouvel_adherent = {
                    "nom": nom,
                    "prenom": prenom,
                    "email": email,
                    "telephone": telephone,
                    "statut": statut,
                    "cotisation_ok": cotisation
                }
                supabase.table("membres").insert(nouvel_adherent).execute()
                st.success(f"Membre {prenom} {nom} ajouté avec succès !")
            else:
                st.warning("Le nom et le prénom sont obligatoires.")

# ---------------------------------------------------------
# 3. MODIFICATION / SUPPRESSION
# ---------------------------------------------------------
elif choice == "Modifier / Supprimer":
    st.subheader("✏️ Editer la fiche d'un membre")
    
    response = supabase.table("membres").select("*").execute()
    data = response.data
    
    if data:
        # Sélection du membre
        membres_dict = {f"{m['nom']} {m['prenom']} (ID: {m['id']})": m for m in data}
        selected_name = st.selectbox("Sélectionnez un membre", list(membres_dict.keys()))
        selected_member = membres_dict[selected_name]
        
        st.divider()
        
        col1, col2 = st.columns(2)
        with col1:
            new_nom = st.text_input("Nom", value=selected_member["nom"])
            new_prenom = st.text_input("Prénom", value=selected_member["prenom"])
            new_email = st.text_input("Email", value=selected_member.get("email", ""))
        with col2:
            new_tel = st.text_input("Téléphone", value=selected_member.get("telephone", ""))
            
            statut_list = ["Actif", "Inactif", "Bureau", "Honneur"]
            current_statut_idx = statut_list.index(selected_member["statut"]) if selected_member.get("statut") in statut_list else 0
            new_statut = st.selectbox("Statut", statut_list, index=current_statut_idx)
            
            new_cotisation = st.checkbox("Cotisation à jour", value=selected_member.get("cotisation_ok", False))

        btn_col1, btn_col2 = st.columns([1, 4])
        with btn_col1:
            if st.button("💾 Mettre à jour"):
                updated_data = {
                    "nom": new_nom,
                    "prenom": new_prenom,
                    "email": new_email,
                    "telephone": new_tel,
                    "statut": new_statut,
                    "cotisation_ok": new_cotisation
                }
                supabase.table("membres").update(updated_data).eq("id", selected_member["id"]).execute()
                st.success("Fiche mise à jour !")
                st.rerun()

        with btn_col2:
            if st.button("🗑️ Supprimer ce membre", type="primary"):
                supabase.table("membres").delete().eq("id", selected_member["id"]).execute()
                st.warning("Membre supprimé.")
                st.rerun()