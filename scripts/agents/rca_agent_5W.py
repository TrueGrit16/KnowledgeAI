from fastapi import FastAPI
from pydantic import BaseModel
from scripts.logconf import logging
from scripts.agents.shared import vectordb, client

app = FastAPI()

class RCARequest(BaseModel):
    topic: str  

@app.post("/rca")
def root_cause_analysis(req: RCARequest):
    try:
        logging.info(f"🔥 RCA request: {req.topic}")
        docs = vectordb.similarity_search(req.topic, k=8)
        context = "\n---\n".join([d.page_content for d in docs])
        prompt = f"""You're an SRE assistant performing Root Cause Analysis using the 5 Whys technique:
        Only use the provided context. Do not make assumptions. If context is missing, say "insufficient context to answer".
        
Context:
{context}

Based on the information above, answer the following:
1. What happened?
2. Why did it happen? (1st Why)
3. Why did that happen? (2nd Why)
4. Why did that happen? (3rd Why)
5. Why did that happen? (4th Why)
6. Why did that happen? (5th Why)
7. What is the actual root cause?

Give clear, numbered answers.
"""
        res = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "system", "content": prompt}]
        )
        return {"rca": res.choices[0].message.content.strip()}
    except Exception:
        logging.exception("RCA agent failed")
        return {"rca": "Error processing RCA"}
