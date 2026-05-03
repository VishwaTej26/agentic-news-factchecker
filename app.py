import streamlit as st
import hashlib
from datetime import datetime
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from agents.factcheck_agent import factcheck_claim, is_valid_claim
from agents.memory_agent import store_article, search_similar, get_past_verdict
from agents.entity_tracker_agent import load_entities, update_entity, save_entities
from utils.helpers import format_verdict_emoji
from config import OPENAI_API_KEY, LLM_MODEL


# uses chatgpt api

st.set_page_config(
    page_title="Agentic News Fact-Checker",
    page_icon="🔍",
    layout="wide"
)

llm = ChatOpenAI(model=LLM_MODEL, temperature=0.0, openai_api_key=OPENAI_API_KEY)

extract_prompt = ChatPromptTemplate.from_template("""
Extract entities and sub-claims from this claim.

Claim: {claim}

Respond in this exact format:
ENTITIES: entity1, entity2, entity3
SUBCLAIMS: subclaim1 | subclaim2
TOPIC: one word topic
""")

predict_prompt = ChatPromptTemplate.from_template("""
Based on this claim and its fact-check verdict, generate 2 short falsifiable predictions about how this story might develop.

Claim: {claim}
Verdict: {verdict}
Reasoning: {reasoning}

Respond in this exact format:
PREDICTION: prediction text
CONFIDENCE: 0.0 to 1.0
TIMEFRAME: e.g. within 1 week
---
PREDICTION: prediction text
CONFIDENCE: 0.0 to 1.0
TIMEFRAME: e.g. within 1 month
""")

def extract_entities(claim: str) -> dict:
    try:
        chain = extract_prompt | llm
        response = chain.invoke({"claim": claim})
        result = {"entities": [], "subclaims": [], "topic": "general"}
        for line in response.content.strip().split("\n"):
            if line.startswith("ENTITIES:"):
                result["entities"] = [e.strip() for e in line.replace("ENTITIES:", "").split(",") if e.strip()]
            elif line.startswith("SUBCLAIMS:"):
                result["subclaims"] = [s.strip() for s in line.replace("SUBCLAIMS:", "").split("|") if s.strip()]
            elif line.startswith("TOPIC:"):
                result["topic"] = line.replace("TOPIC:", "").strip()
        return result
    except Exception as e:
        return {"entities": [], "subclaims": [], "topic": "general"}

def generate_predictions(claim: str, verdict: str, reasoning: str) -> list:
    try:
        chain = predict_prompt | llm
        response = chain.invoke({"claim": claim, "verdict": verdict, "reasoning": reasoning})
        predictions = []
        for block in response.content.strip().split("---"):
            pred = {"prediction": "", "confidence": 0.0, "timeframe": ""}
            for line in block.strip().split("\n"):
                if line.startswith("PREDICTION:"):
                    pred["prediction"] = line.replace("PREDICTION:", "").strip()
                elif line.startswith("CONFIDENCE:"):
                    try:
                        pred["confidence"] = float(line.replace("CONFIDENCE:", "").strip())
                    except:
                        pred["confidence"] = 0.0
                elif line.startswith("TIMEFRAME:"):
                    pred["timeframe"] = line.replace("TIMEFRAME:", "").strip()
            if pred["prediction"]:
                predictions.append(pred)
        return predictions
    except Exception as e:
        return []

# ── UI ────────────────────────────────────────────────────────────────────────

st.title("🔍 Agentic News Fact-Checker")
st.caption("Enter any news claim — AI agents will analyze it in real time")

claim_input = st.text_area(
    "Enter a news claim or headline",
    placeholder="e.g. Apple announced WWDC 2026 for June 8-12",
    height=120
)

if st.button("🚀 Run Agents", type="primary", use_container_width=True):
    if not claim_input.strip():
        st.warning("Please enter a claim.")
    elif not is_valid_claim(claim_input):
        st.warning("Please enter a more specific claim.")
    else:
        st.divider()

        with st.status("🤖 Agents working...", expanded=True) as status:

            # AGENT 1: PREPROCESSOR
            st.write("### 🧹 Agent 1 — Preprocessor")
            st.write("Extracting entities and sub-claims...")
            extracted = extract_entities(claim_input)
            entities = extracted["entities"]
            subclaims = extracted["subclaims"]
            topic = extracted["topic"]
            st.write(f"✅ **{len(entities)} entities** found: {', '.join(entities) if entities else 'none'}")
            st.write(f"✅ **{len(subclaims)} sub-claims** identified")
            st.write(f"✅ Topic: **{topic}**")

            # AGENT 2: MEMORY CHECK
            st.write("### 🧠 Agent 2 — Memory Agent")
            st.write("Checking vector database for similar past claims...")
            past = get_past_verdict(claim_input)
            if past:
                st.warning("⚡ Similar claim found in memory — enriching analysis with past context")
                st.caption(f"Previous verdict: **{past.get('main_verdict','unknown').upper()}** | Confidence: {float(past.get('main_confidence', 0))*100:.0f}%")
            else:
                st.write("✅ No previous match — running fresh analysis")
            similar = search_similar(claim_input, n_results=3)
            similar_docs = similar.get("documents", [[]])[0] if similar else []
            if similar_docs and any(d for d in similar_docs):
                st.write(f"✅ **{len(similar_docs)} related claims** found in memory")
            else:
                st.write("✅ Memory search complete")

            # AGENT 3: FACT-CHECK
            st.write("### 🔍 Agent 3 — Fact-Check Agent")
            st.write("Searching live web sources and generating verdict...")
            main_result = factcheck_claim(claim_input)
            verdict = main_result.get("verdict", "unverified")
            confidence = main_result.get("confidence", 0.0)
            reasoning = main_result.get("reasoning", "")
            sources = main_result.get("sources", [])
            st.write(f"✅ **{len(sources)} sources** searched")
            st.write(f"✅ Verdict: **{verdict.upper()}** at **{int(confidence*100)}% confidence**")

            sub_results = []
            if subclaims:
                st.write(f"Verifying {len(subclaims)} sub-claims...")
                for sc in subclaims[:2]:
                    if is_valid_claim(sc):
                        sr = factcheck_claim(sc)
                        sub_results.append(sr)
                        emoji = format_verdict_emoji(sr["verdict"])
                        st.write(f"  {emoji} *{sc[:70]}* → **{sr['verdict'].upper()}** ({int(sr['confidence']*100)}%)")

            # AGENT 4: MEMORY STORAGE
            st.write("### 💾 Agent 4 — Memory Storage")
            st.write("Storing claim and verdict in ChromaDB...")
            article_obj = {
                "title": claim_input,
                "content": claim_input,
                "source": "manual",
                "url": "",
                "published_at": datetime.utcnow().isoformat(),
                "topic": topic,
                "hash": hashlib.md5(claim_input.encode()).hexdigest(),
                "ingested_at": datetime.utcnow().isoformat(),
                "entities": entities,
                "claims": [claim_input] + subclaims,
                "verdicts": [main_result] + sub_results,
                "origin": "manual"
            }
            store_article(article_obj)
            st.write("✅ Stored in vector database — will improve future checks")

            # AGENT 5: ENTITY TRACKER
            st.write("### 👤 Agent 5 — Entity Tracker")
            st.write("Updating entity credibility profiles...")
            all_entities = load_entities()
            for entity in entities:
                all_entities = update_entity(all_entities, entity, article_obj)
            save_entities(all_entities)
            st.write(f"✅ Updated **{len(entities)} entity profiles**")

            # PREDICTIONS
            st.write("### 🔮 Prediction Agent")
            st.write("Generating predictions about how this story develops...")
            predictions = generate_predictions(claim_input, verdict, reasoning)
            st.write(f"✅ **{len(predictions)} predictions** generated")

            status.update(label="✅ All agents complete!", state="complete")

        # ── RESULTS ──────────────────────────────────────────────────────────
        st.divider()
        st.subheader("📊 Verdict")

        emoji = format_verdict_emoji(verdict)
        col1, col2 = st.columns([3, 1])
        with col1:
            if verdict == "true":
                st.success(f"## {emoji} TRUE")
            elif verdict == "false":
                st.error(f"## {emoji} FALSE")
            else:
                st.warning(f"## {emoji} UNVERIFIED")
        with col2:
            st.metric("Confidence", f"{int(confidence*100)}%")

        st.markdown(f"**Reasoning:** {reasoning}")

        if sub_results:
            st.subheader("🔬 Sub-claim Breakdown")
            for sr in sub_results:
                e = format_verdict_emoji(sr["verdict"])
                st.write(f"{e} **{sr['claim'][:100]}**")
                st.caption(f"{sr['verdict'].upper()} — {int(sr['confidence']*100)}% — {sr.get('reasoning', '')}")

        if sources:
            with st.expander("📚 Sources used"):
                for i, s in enumerate(sources):
                    st.markdown(f"**Source {i+1}:** [{s['source']}]({s['url']})")
                    st.caption(s['text'][:200])

        if predictions:
            st.divider()
            st.subheader("🔮 How this story might develop")
            for pred in predictions:
                conf = pred.get("confidence", 0.0)
                text = f"**{pred['prediction']}**\n\n_{pred['timeframe']} — {int(conf*100)}% confidence_"
                if conf > 0.7:
                    st.success(text)
                elif conf > 0.4:
                    st.warning(text)
                else:
                    st.info(text)

# ── PAST CLAIMS MEMORY ───────────────────────────────────────────────────────
st.divider()
st.subheader("🧠 Previously Checked Claims")

try:
    recent = search_similar("news claim fact check", n_results=10)
    docs = recent.get("documents", [[]])[0] if recent else []
    metas = recent.get("metadatas", [[]])[0] if recent else []

    if not metas:
        st.info("No claims checked yet. Run your first fact-check above!")
    else:
        for meta in metas:
            verdict = meta.get("main_verdict", "unverified")
            confidence = float(meta.get("main_confidence", 0.0))
            title = meta.get("title", "Unknown claim")
            topic = meta.get("topic", "general")
            ingested = meta.get("ingested_at", "")[:10]
            emoji = format_verdict_emoji(verdict)

            col1, col2, col3 = st.columns([5, 2, 1])
            with col1:
                st.write(f"**{title[:80]}**")
                st.caption(f"Topic: {topic} | Checked: {ingested}")
            with col2:
                if verdict == "true":
                    st.success(f"{emoji} TRUE")
                elif verdict == "false":
                    st.error(f"{emoji} FALSE")
                else:
                    st.warning(f"{emoji} UNVERIFIED")
            with col3:
                st.metric("", f"{int(confidence*100)}%")
            st.divider()
except Exception as e:
    st.info("No claims checked yet.")
