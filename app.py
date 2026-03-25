import streamlit as st
from agents.factcheck_agent import factcheck_claim, is_valid_claim
from agents.preprocessor_agent import preprocess_article
from agents.memory_agent import run_memory_storage, search_similar
from agents.entity_tracker_agent import load_entities
from utils.helpers import format_verdict_emoji, format_confidence_bar, get_latest_run, get_predictions
import json

st.set_page_config(
    page_title="Agentic News Fact-Checker",
    page_icon="🔍",
    layout="wide"
)

st.title("🔍 Agentic News Fact-Checker")
st.caption("AI-powered real-time news analysis and fact-checking system")

tabs = st.tabs([
    "🔎 Fact Check",
    "📰 Analyze Article",
    "🧠 Memory & Entities",
    "📊 Latest Run",
    "🔮 Predictions"
])

# TAB 1: Manual claim fact check
with tabs[0]:
    st.header("Check a Claim")
    st.write("Enter any news claim or headline to verify it.")
    
    claim_input = st.text_area(
        "Enter claim here",
        placeholder="e.g. Apple announced WWDC 2026 for June 8-12",
        height=100
    )
    
    if st.button("🔍 Fact Check", type="primary"):
        if not claim_input.strip():
            st.warning("Please enter a claim to check.")
        elif not is_valid_claim(claim_input):
            st.warning("Please enter a more specific claim.")
        else:
            with st.spinner("Searching sources and analyzing..."):
                result = factcheck_claim(claim_input)
            
            verdict = result.get("verdict", "unverified")
            confidence = result.get("confidence", 0.0)
            reasoning = result.get("reasoning", "")
            sources = result.get("sources", [])
            
            emoji = format_verdict_emoji(verdict)
            
            col1, col2 = st.columns(2)
            with col1:
                if verdict == "true":
                    st.success(f"{emoji} Verdict: TRUE")
                elif verdict == "false":
                    st.error(f"{emoji} Verdict: FALSE")
                else:
                    st.warning(f"{emoji} Verdict: UNVERIFIED")
            with col2:
                st.metric("Confidence", f"{int(confidence*100)}%")
            
            st.markdown(f"**Reasoning:** {reasoning}")
            
            if sources:
                with st.expander("📚 Sources used"):
                    for i, s in enumerate(sources):
                        st.markdown(f"**Source {i+1}:** [{s['source']}]({s['url']})")
                        st.caption(s['text'][:200])

# TAB 2: Paste full article
with tabs[1]:
    st.header("Analyze a Full Article")
    st.write("Paste a full news article to extract claims and fact-check them.")
    
    title_input = st.text_input("Article Title", placeholder="Enter article title...")
    article_input = st.text_area(
        "Paste article content here",
        placeholder="Paste the full article text...",
        height=300
    )
    
    if st.button("🧪 Analyze Article", type="primary"):
        if not article_input.strip():
            st.warning("Please paste article content.")
        else:
            with st.spinner("Extracting entities and claims..."):
                article = {
                    "title": title_input or "Untitled",
                    "content": article_input,
                    "source": "manual",
                    "url": "",
                    "published_at": "",
                    "topic": "manual",
                    "hash": str(hash(article_input))[:16],
                }
                processed = preprocess_article(article)
            
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("🏷️ Entities Found")
                entities = processed.get("entities", [])
                if entities:
                    for e in entities:
                        st.badge(e)
                else:
                    st.write("No entities found.")
            with col2:
                st.subheader("🤖 AI Origin Detection")
                origin = processed.get("origin", "unknown")
                if origin == "ai":
                    st.error("⚠️ Likely AI-generated")
                elif origin == "human":
                    st.success("✅ Likely human-written")
                else:
                    st.warning("❓ Unknown origin")
            
            st.subheader("📋 Claims Extracted")
            claims = processed.get("claims", [])
            if claims:
                for i, claim in enumerate(claims):
                    if not is_valid_claim(claim):
                        continue
                    with st.expander(f"Claim {i+1}: {claim[:80]}..."):
                        with st.spinner("Fact-checking..."):
                            result = factcheck_claim(claim)
                        verdict = result.get("verdict", "unverified")
                        confidence = result.get("confidence", 0.0)
                        emoji = format_verdict_emoji(verdict)
                        if verdict == "true":
                            st.success(f"{emoji} TRUE — {int(confidence*100)}% confidence")
                        elif verdict == "false":
                            st.error(f"{emoji} FALSE — {int(confidence*100)}% confidence")
                        else:
                            st.warning(f"{emoji} UNVERIFIED — {int(confidence*100)}% confidence")
                        st.write(result.get("reasoning", ""))
            else:
                st.write("No claims extracted.")

# TAB 3: Memory and Entities
with tabs[2]:
    st.header("🧠 Entity Memory")
    st.write("Entities tracked across all processed articles.")
    
    entities = load_entities()
    if not entities:
        st.info("No entities tracked yet. Run the pipeline first.")
    else:
        search = st.text_input("Search entity", placeholder="e.g. Apple, Trump, OpenAI")
        
        filtered = {
            k: v for k, v in entities.items()
            if search.lower() in k.lower()
        } if search else entities
        
        sorted_entities = sorted(
            filtered.values(),
            key=lambda x: x["mention_count"],
            reverse=True
        )[:20]
        
        for entity in sorted_entities:
            with st.expander(f"**{entity['name']}** — {entity['mention_count']} mentions"):
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Credibility Score", f"{entity['credibility_score']*100:.0f}%")
                with col2:
                    st.metric("True Claims", entity['verdicts']['true'])
                with col3:
                    st.metric("False Claims", entity['verdicts']['false'])
                st.caption(f"First seen: {entity['first_seen'][:10]} | Last seen: {entity['last_seen'][:10]}")

# TAB 4: Latest Pipeline Run
with tabs[3]:
    st.header("📊 Latest Pipeline Run")
    
    run_data = get_latest_run()
    if not run_data:
        st.info("No pipeline run yet. Run python pipeline.py first.")
    else:
        st.metric("Articles Processed", run_data.get("articles_processed", 0))
        st.caption(f"Run at: {run_data.get('run_at', 'unknown')}")
        
        articles = run_data.get("articles", [])
        for article in articles[:10]:
            verdicts = article.get("verdicts", [])
            if not verdicts:
                continue
            with st.expander(f"📰 {article.get('title', 'Untitled')[:80]}"):
                st.caption(f"Source: {article.get('source')} | Topic: {article.get('topic')}")
                st.caption(f"Origin: {article.get('origin', 'unknown')} | Entities: {', '.join(article.get('entities', [])[:5])}")
                for v in verdicts:
                    emoji = format_verdict_emoji(v.get("verdict", "unverified"))
                    st.write(f"{emoji} **{v.get('claim', '')[:80]}**")
                    st.write(f"Confidence: {int(v.get('confidence', 0)*100)}% — {v.get('reasoning', '')}")

# TAB 5: Predictions
with tabs[4]:
    st.header("🔮 Predictions")
    st.write("AI-generated falsifiable predictions based on recent news patterns.")
    
    predictions = get_predictions()
    if not predictions:
        st.info("No predictions yet. Run the pipeline first.")
    else:
        for i, pred in enumerate(predictions):
            confidence = pred.get("confidence", 0.0)
            if confidence > 0.7:
                st.success(f"**Prediction {i+1}:** {pred.get('prediction', '')}")
            elif confidence > 0.4:
                st.warning(f"**Prediction {i+1}:** {pred.get('prediction', '')}")
            else:
                st.info(f"**Prediction {i+1}:** {pred.get('prediction', '')}")
            col1, col2 = st.columns(2)
            with col1:
                st.caption(f"Confidence: {int(confidence*100)}%")
            with col2:
                st.caption(f"Timeframe: {pred.get('timeframe', 'unknown')}")