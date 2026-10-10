"""
Online Deal Scouter: Interactive Gradio Web Dashboard.
Features live streaming agent logs, 3D latent space visualization,
and autonomous deal monitoring with instant push notifications.
"""

import logging
import queue
import threading
import time
import gradio as gr
import plotly.graph_objects as go

from deal_agent_framework import DealAgentFramework
from log_utils import reformat


class QueueHandler(logging.Handler):
    def __init__(self, log_queue):
        super().__init__()
        self.log_queue = log_queue

    def emit(self, record):
        self.log_queue.put(self.format(record))


def html_for(log_data):
    recent_logs = '<br>'.join(log_data[-22:])
    return f"""
    <div id="scrollContent" style="height: 380px; overflow-y: auto; border: 1px solid #44475a; 
         background-color: #282a36; color: #f8f8f2; font-family: monospace; font-size: 13px; 
         padding: 12px; border-radius: 8px;">
        {recent_logs}
    </div>
    """


def setup_logging(log_queue):
    handler = QueueHandler(log_queue)
    formatter = logging.Formatter(
        "[%(asctime)s] %(message)s",
        datefmt="%H:%M:%S",
    )
    handler.setFormatter(formatter)
    logger = logging.getLogger()
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


class App:

    def __init__(self):
        self.agent_framework: DealAgentFramework | None = None

    def get_agent_framework(self) -> DealAgentFramework:
        if not self.agent_framework:
            self.agent_framework = DealAgentFramework()
            self.agent_framework.init_agents_as_needed()
        return self.agent_framework

    def run(self):
        with gr.Blocks(title="Online Deal Scouter", fill_width=True) as ui:
            log_data = gr.State([])

            def table_for(opps):
                return [
                    [
                        opp.deal.product_description,
                        f"${opp.deal.price:.2f}",
                        f"${opp.estimate:.2f}",
                        f"${opp.discount:.2f}",
                        opp.deal.url
                    ]
                    for opp in opps
                ]

            def update_output(current_logs, log_q, result_q):
                initial_table = table_for(self.get_agent_framework().memory)
                final_table = None

                while True:
                    try:
                        msg = log_q.get_nowait()
                        current_logs.append(reformat(msg))
                        yield current_logs, html_for(current_logs), final_table or initial_table
                    except queue.Empty:
                        try:
                            final_table = result_q.get_nowait()
                            yield current_logs, html_for(current_logs), final_table or initial_table
                        except queue.Empty:
                            if final_table is not None:
                                break
                            time.sleep(0.1)

            def get_plot():
                documents, vectors, colors = DealAgentFramework.get_plot_data(max_datapoints=1000)
                fig = go.Figure(data=[go.Scatter3d(
                    x=vectors[:, 0],
                    y=vectors[:, 1],
                    z=vectors[:, 2],
                    mode='markers',
                    marker=dict(size=3, color=colors, opacity=0.8),
                    text=documents,
                    hoverinfo='text'
                )])

                fig.update_layout(
                    title="Retail Embedding Latent Space (ChromaDB t-SNE)",
                    scene=dict(
                        xaxis_title='Dim 1',
                        yaxis_title='Dim 2',
                        zaxis_title='Dim 3',
                        aspectmode='manual',
                        aspectratio=dict(x=1.8, y=1.8, z=1),
                        camera=dict(eye=dict(x=1.5, y=1.5, z=0.8))
                    ),
                    height=380,
                    margin=dict(r=0, b=0, l=0, t=30),
                    paper_bgcolor='#1e1f29',
                    font=dict(color='#f8f8f2')
                )
                return fig

            def do_run():
                opportunities = self.get_agent_framework().run()
                return table_for(opportunities)

            def run_with_logging(existing_logs):
                log_q = queue.Queue()
                result_q = queue.Queue()
                setup_logging(log_q)

                def worker():
                    res = do_run()
                    result_q.put(res)

                thread = threading.Thread(target=worker, daemon=True)
                thread.start()

                for logs, html, table in update_output(existing_logs, log_q, result_q):
                    yield logs, html, table

            def do_select(selected_index: gr.SelectData):
                opportunities = self.get_agent_framework().memory
                row = selected_index.index[0]
                if row < len(opportunities):
                    opp = opportunities[row]
                    self.get_agent_framework().planner.messenger.alert(opp)

            with gr.Row():
                gr.Markdown(
                    '<div style="text-align: center; font-size: 28px; font-weight: bold; margin-bottom: 4px;">'
                    'Online Deal Scouter</div>'
                    '<div style="text-align: center; font-size: 15px; color: #8be9fd; margin-bottom: 12px;">'
                    'Autonomous Multi-Agent Retail Arbitrage & Real-Time Price Prediction Platform</div>'
                )

            with gr.Row():
                opportunities_table = gr.Dataframe(
                    headers=["Product Description", "Listed Price", "Estimated Value", "Discount Margin", "Deal URL"],
                    wrap=True,
                    column_widths=[5, 1, 1, 1, 2],
                    row_count=10,
                    col_count=5,
                    max_height=350,
                )

            with gr.Row():
                with gr.Column(scale=1):
                    gr.Markdown("### Real-Time Multi-Agent Execution Log")
                    logs_view = gr.HTML()
                with gr.Column(scale=1):
                    gr.Markdown("### Product Latent Space (3D Embedding Space)")
                    plot_view = gr.Plot(value=get_plot(), show_label=False)

            ui.load(run_with_logging, inputs=[log_data], outputs=[log_data, logs_view, opportunities_table])

            # Periodic background scanner cycle every 5 minutes
            timer = gr.Timer(value=300, active=True)
            timer.tick(run_with_logging, inputs=[log_data], outputs=[log_data, logs_view, opportunities_table])

            opportunities_table.select(do_select)

        ui.launch(share=False, inbrowser=True)


if __name__ == "__main__":
    App().run()
