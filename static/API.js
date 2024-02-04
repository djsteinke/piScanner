var MYAPI = {
    GET: function(endpoint, successCallback) {
        return $.ajax({
            type: "GET",
            async: true,
            url: endpoint,
            contentType: 'application/json',
            async: true,
            callback: successCallback,
            success: function(data, status) {
                if (this.callback != null)
                    this.callback(data)
            },
            error: function(response, status, error) {
                alert('Error');
            }
        });
    },
    POST: function(endpoint, successCallback, data) {
        if (typeof data == typeof {})
            data = JSON.stringify(data);
        return $.ajax({
            type: "POST",
            async: true,
            url: endpoint,
            contentType: 'application/json',
            data: data,
            callback: successCallback,
            success: function(data, status) {
                if (this.callback != null)
                    this.callback(data)
            },
            error: function(response, status, error) {
                alert('Error');
            }
        });
    }
}