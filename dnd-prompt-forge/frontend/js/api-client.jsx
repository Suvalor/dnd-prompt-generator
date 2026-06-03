/* ApiClient — 前端与后端 API 通信层，暴露 window.ApiClient 全局对象
   提供 bootstrap / generatePrompt / getQuota / fingerprint / feedback 等方法 */

(function () {
  /** API 基础路径，默认同域，可通过 window.__API_BASE__ 覆盖 */
  var API_BASE = window.__API_BASE__ || '';

  /** 内部状态：CSRF token、features 配置、session 就绪标记、指纹缓存 */
  var _csrfToken = null;
  var _features = null;
  var _sessionReady = false;
  var _fingerprintCache = null;

  /** 将空字符串转为 null，用于 Optional 字段 */
  function emptyToNull(val) {
    if (val === '' || val === undefined) return null;
    return val;
  }

  /** 带超时的 fetch 封装，超时后抛出 Error */
  function fetchWithTimeout(url, options, timeoutMs) {
    var controller = new AbortController();
    var signal = controller.signal;
    var timeoutId = setTimeout(function () { controller.abort(); }, timeoutMs);
    var merged = Object.assign({}, options, { signal: signal, credentials: 'include' });
    return fetch(url, merged).then(function (response) {
      clearTimeout(timeoutId);
      return response;
    }).catch(function (err) {
      clearTimeout(timeoutId);
      if (err.name === 'AbortError') {
        throw new Error('Request timed out');
      }
      throw err;
    });
  }

  /** 构建带 CSRF header 的请求选项 */
  function withCsrf(options) {
    var headers = Object.assign({}, options.headers || {}, { 'x-csrf-token': _csrfToken });
    return Object.assign({}, options, { headers: headers });
  }

  /** POST /api/session/bootstrap — 初始化 session，获取 CSRF token 和 features */
  function bootstrap() {
    return fetchWithTimeout(API_BASE + '/api/session/bootstrap', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
    }, 5000).then(function (response) {
      if (!response.ok) throw new Error('Bootstrap failed: ' + response.status);
      return response.json();
    }).then(function (data) {
      _csrfToken = data.csrf_token || null;
      _features = data.features || null;
      _sessionReady = true;
      return { csrf_token: _csrfToken, features: _features };
    }).catch(function (err) {
      _sessionReady = false;
      throw err;
    });
  }

  /** 处理 401/403 响应：重新 bootstrap 后重试原请求（最多1次） */
  function handleAuthRetry(response, retryFn) {
    if (response.status === 401 || response.status === 403) {
      return bootstrap().then(function () {
        return retryFn();
      });
    }
    return response.json().then(function (data) {
      var err = new Error(data.detail || 'Request failed');
      err.status = response.status;
      throw err;
    });
  }

  /** POST /api/generate-prompt — 调用后端生成提示词，携带 CSRF header */
  function generatePrompt(formData) {
    /** 内部重试闭包 */
    function doCall(isRetry) {
      if (!_csrfToken) {
        return bootstrap().then(function () { return doCall(false); });
      }
      var opts = withCsrf({
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData),
      });
      return fetchWithTimeout(API_BASE + '/api/generate-prompt', opts, 75000)
        .then(function (response) {
          if (!response.ok) {
            if (!isRetry && (response.status === 401 || response.status === 403)) {
              return handleAuthRetry(response, function () { return doCall(true); });
            }
            return response.json().then(function (data) {
              var err = new Error(data.detail || 'Generate failed');
              err.status = response.status;
              throw err;
            }).catch(function (jsonErr) {
              if (jsonErr.status) throw jsonErr;
              throw new Error('Generate failed: ' + response.status);
            });
          }
          return response.json();
        });
    }
    return doCall(false);
  }

  /** GET /api/quota — 查询当前配额状态 */
  function getQuota() {
    return fetchWithTimeout(API_BASE + '/api/quota', {
      method: 'GET',
    }, 3000).then(function (response) {
      if (!response.ok) throw new Error('Quota check failed');
      return response.json();
    });
  }

  /** 使用 crypto.subtle SHA-256 生成浏览器指纹哈希，结果缓存 */
  function getFingerprintHash() {
    if (_fingerprintCache !== null) return Promise.resolve(_fingerprintCache);
    if (!window.crypto || !window.crypto.subtle) {
      _fingerprintCache = '';
      return Promise.resolve('');
    }
    var raw = [
      navigator.userAgent || '',
      navigator.language || '',
      screen.width + 'x' + screen.height,
      screen.colorDepth || '',
      new Date().getTimezoneOffset(),
      navigator.hardwareConcurrency || '',
    ].join('|');
    var encoder = new TextEncoder();
    var data = encoder.encode(raw);
    return crypto.subtle.digest('SHA-256', data).then(function (hashBuffer) {
      var hashArray = Array.from(new Uint8Array(hashBuffer));
      var hex = hashArray.map(function (b) { return b.toString(16).padStart(2, '0'); }).join('');
      _fingerprintCache = hex;
      return hex;
    }).catch(function () {
      _fingerprintCache = '';
      return '';
    });
  }

  /** 返回 session 是否就绪 */
  function isSessionReady() {
    return _sessionReady;
  }

  /** 返回 features 配置 */
  function getFeatures() {
    return _features;
  }

  /** 前端表单字段映射到后端 API 字段，fingerprintHash 由调用方传入 */
  function mapFormToApi(form, fingerprintHash) {
    return {
      output_type: form.type || 'portrait',
      race: form.race || '',
      class_role: form.klass || '',
      style: form.style || 'painterly',
      mood: form.mood || 'brooding',
      description: form.desc || '',
      target_model: form.model || 'midjourney',
      gender: emptyToNull(form.gender),
      age: emptyToNull(form.age),
      alignment: emptyToNull(form.alignment),
      armor: emptyToNull(form.armor),
      weapon: emptyToNull(form.weapon),
      magic: emptyToNull(form.magic),
      palette: emptyToNull(form.palette),
      camera: emptyToNull(form.camera),
      /** 后端可选字段：角色背景描述 */
      background: emptyToNull(form.background),
      client_fingerprint_hash: fingerprintHash || null,
      fallback_prompt_preview: null,
    };
  }

  /** 后端响应映射到前端 result 对象 */
  function mapApiToResult(response) {
    return {
      main: response.main_prompt || '',
      short: response.short_prompt || '',
      negative: response.negative_prompt || '',
      styleNote: response.style_notes || '',
      tip: response.usage_tip || '',
      tokenNote: null,
      mode: response.mode || 'fallback',
      requestId: response.request_id || null,
      quota: response.quota || null,
      meta: { model: '', template: '', rules: '' },
    };
  }

  /** POST /api/feedback — 提交用户反馈 */
  function submitFeedback(data) {
    if (!_csrfToken) {
      return bootstrap().then(function () { return submitFeedback(data); });
    }
    var opts = withCsrf({
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    return fetchWithTimeout(API_BASE + '/api/feedback', opts, 5000)
      .then(function (response) {
        if (!response.ok) throw new Error('Feedback failed');
        return response.json();
      });
  }

  /** 暴露到 window.ApiClient */
  window.ApiClient = {
    bootstrap: bootstrap,
    generatePrompt: generatePrompt,
    getQuota: getQuota,
    getFingerprintHash: getFingerprintHash,
    isSessionReady: isSessionReady,
    getFeatures: getFeatures,
    mapFormToApi: mapFormToApi,
    mapApiToResult: mapApiToResult,
    submitFeedback: submitFeedback,
  };
})();
