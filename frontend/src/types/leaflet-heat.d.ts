import type * as Leaflet from 'leaflet';

declare module 'leaflet' {
  interface HeatLayerOptions {
    radius?: number;
    blur?: number;
    maxZoom?: number;
    max?: number;
    minOpacity?: number;
    gradient?: Record<number, string>;
  }

  interface HeatLayer extends Leaflet.Layer {
    setLatLngs(pontos: Array<[number, number, number?]>): this;
    addLatLng(ponto: [number, number, number?]): this;
  }

  function heatLayer(
    pontos: Array<[number, number, number?]>,
    opcoes?: HeatLayerOptions,
  ): HeatLayer;
}
