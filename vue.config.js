module.exports = {
  // 选项...
	publicPath: './',
    devServer: {
      open: true,
      host:"localhost",
      port: 8080,
      https: false,
      proxy: {
        '/api': {
          target: 'http://192.168.108.102:8984/',
          ws: true,
          changeOrigin: true,
		  secure: false,
		  pathRewrite: {
			  '^/api': ''
		  }
        },
      }
    }
}