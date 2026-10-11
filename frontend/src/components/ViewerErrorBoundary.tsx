import { Component, type ReactNode } from "react";

export class ViewerErrorBoundary extends Component<{
  children: ReactNode;
  onReturn: () => void;
}, { failed: boolean }> {
  state = { failed: false };
  static getDerivedStateFromError() { return { failed: true }; }

  render() {
    if (this.state.failed) {
      return (
        <div className="viewer-error" role="alert">
          <strong>No se pudo abrir el modelo 3D</strong>
          <p>Compruebe la conexión con la API y que su navegador admite WebGL.
            Puede volver al mapa y generar otro escenario.</p>
          <button onClick={this.props.onReturn}>Volver al mapa</button>
        </div>
      );
    }
    return this.props.children;
  }
}
