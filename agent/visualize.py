import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent.graph import build_graph


def save_graph_image(output_path="graph_visualization1.png"):
    graph = build_graph()
    try:
        img = graph.get_graph().draw_mermaid_png()
        with open(output_path, "wb") as f:
            f.write(img)
        print(f"그래프 이미지 저장 완료: {output_path}")
    except Exception as e:
        print(f"PNG 저장 실패: {e}")
        print("Mermaid 텍스트로 대체 저장합니다.")
        mermaid = graph.get_graph().draw_mermaid()
        with open("graph_visualization.md", "w", encoding="utf-8") as f:
            f.write(f"```mermaid\n{mermaid}\n```")
        print("graph_visualization.md 저장 완료")


if __name__ == "__main__":
    save_graph_image()
