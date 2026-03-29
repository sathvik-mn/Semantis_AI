import { useEffect, useRef, useState, useCallback } from 'react'

interface NeonRGBTextEffectProps {
  /** Lines of text to render. Each string = one line. */
  lines?: string[]
  fontSize?: number
  fontFamily?: string
  fontWeight?: number
  className?: string
  offsetAmount?: number
}

export function NeonRGBTextEffect({
  lines = ['Cut Your LLM Costs', 'By Up To 80%'],
  fontSize = 72,
  fontFamily = "'Inter', sans-serif",
  fontWeight = 800,
  className = '',
  offsetAmount = 0.005,
}: NeonRGBTextEffectProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const containerRef = useRef<HTMLDivElement>(null)
  const [dimensions, setDimensions] = useState({ width: 800, height: 200 })

  const measure = useCallback(() => {
    const c = document.createElement('canvas')
    const ctx = c.getContext('2d')!
    ctx.font = `${fontWeight} ${fontSize}px ${fontFamily}`

    let maxWidth = 0
    for (const line of lines) {
      const m = ctx.measureText(line)
      if (m.width > maxWidth) maxWidth = m.width
    }

    const lineHeight = fontSize * 1.2
    const totalHeight = lineHeight * lines.length + fontSize * 0.3
    const totalWidth = maxWidth + fontSize * 0.4

    setDimensions({ width: Math.ceil(totalWidth), height: Math.ceil(totalHeight) })
  }, [lines, fontSize, fontFamily, fontWeight])

  useEffect(() => { measure() }, [measure])

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return

    const dpr = Math.min(window.devicePixelRatio || 1, 2)
    canvas.width = Math.round(dimensions.width * dpr)
    canvas.height = Math.round(dimensions.height * dpr)

    const gl = canvas.getContext('webgl', { alpha: true, premultipliedAlpha: false })
    if (!gl) return

    // --- Shaders ---
    const vertSrc = `
      attribute vec2 position;
      varying vec2 vUv;
      void main() {
        vUv = vec2(position.x * 0.5 + 0.5, 1.0 - (position.y * 0.5 + 0.5));
        gl_Position = vec4(position, 0.0, 1.0);
      }
    `
    const fragSrc = `
      precision mediump float;
      uniform sampler2D uTexture;
      uniform vec2 uOffset;
      uniform vec3 uColor;
      varying vec2 vUv;
      void main() {
        vec2 uv = vUv + vec2(uOffset.x, -uOffset.y);
        vec4 t = texture2D(uTexture, uv);
        gl_FragColor = vec4(uColor * t.a * 1.5, t.a);
      }
    `
    const vs = gl.createShader(gl.VERTEX_SHADER)!
    gl.shaderSource(vs, vertSrc)
    gl.compileShader(vs)

    const fs = gl.createShader(gl.FRAGMENT_SHADER)!
    gl.shaderSource(fs, fragSrc)
    gl.compileShader(fs)

    const prog = gl.createProgram()!
    gl.attachShader(prog, vs)
    gl.attachShader(prog, fs)
    gl.linkProgram(prog)
    gl.useProgram(prog)

    // --- Geometry ---
    const buf = gl.createBuffer()
    gl.bindBuffer(gl.ARRAY_BUFFER, buf)
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1,-1, 1,-1, -1,1, 1,1]), gl.STATIC_DRAW)
    const pos = gl.getAttribLocation(prog, 'position')
    gl.enableVertexAttribArray(pos)
    gl.vertexAttribPointer(pos, 2, gl.FLOAT, false, 0, 0)

    // --- Text texture ---
    const tc = document.createElement('canvas')
    const tctx = tc.getContext('2d')!
    tc.width = canvas.width
    tc.height = canvas.height
    tctx.clearRect(0, 0, tc.width, tc.height)
    tctx.fillStyle = '#ffffff'
    tctx.font = `${fontWeight} ${fontSize * dpr}px ${fontFamily}`
    tctx.textAlign = 'center'
    tctx.textBaseline = 'top'

    const lineHeight = fontSize * 1.2 * dpr
    const startY = (tc.height - lineHeight * lines.length) / 2
    lines.forEach((line, i) => {
      tctx.fillText(line, tc.width / 2, startY + i * lineHeight)
    })

    const tex = gl.createTexture()
    gl.bindTexture(gl.TEXTURE_2D, tex)
    gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, tc)
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR)
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR)
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE)
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE)

    // --- Uniforms ---
    const uTex = gl.getUniformLocation(prog, 'uTexture')
    const uOff = gl.getUniformLocation(prog, 'uOffset')
    const uCol = gl.getUniformLocation(prog, 'uColor')

    // --- Render ---
    gl.enable(gl.BLEND)
    gl.blendFunc(gl.SRC_ALPHA, gl.ONE)
    gl.viewport(0, 0, canvas.width, canvas.height)
    gl.clearColor(0, 0, 0, 0)
    gl.clear(gl.COLOR_BUFFER_BIT)

    const channels = [
      { color: [1, 0, 0], offset: [offsetAmount, 0] },
      { color: [0, 1, 0], offset: [0, 0] },
      { color: [0, 0, 1], offset: [-offsetAmount, 0] },
    ]
    channels.forEach(({ color, offset }) => {
      gl.uniform2fv(uOff, offset)
      gl.uniform3fv(uCol, color)
      gl.uniform1i(uTex, 0)
      gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4)
    })

    return () => {
      gl.deleteProgram(prog)
      gl.deleteShader(vs)
      gl.deleteShader(fs)
      gl.deleteBuffer(buf)
      gl.deleteTexture(tex)
    }
  }, [dimensions, lines, fontSize, fontFamily, fontWeight, offsetAmount])

  return (
    <div
      ref={containerRef}
      className={className}
      style={{ width: dimensions.width, height: dimensions.height, display: 'inline-block' }}
    >
      <canvas
        ref={canvasRef}
        style={{ width: dimensions.width, height: dimensions.height, display: 'block' }}
      />
    </div>
  )
}
