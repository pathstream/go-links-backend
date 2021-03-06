import React from 'react';
import {connect} from 'react-redux';
import * as actions from '../actions';

const { detect } = require('detect-browser');
const browser = detect();


function mapStateToProps(state) {

  state = state.core;

  return {
    errorBarMessage: state.get('errorBarMessage'),
    chromeExtensionInstalled: state.get('chromeExtensionInstalled'),
    userInfo: state.get('userInfo'),
  };
}


export const Butterbar = React.createClass({

  render: function() {
    const CHROME_INSTALLATION_MESSAGE = `
        <a href="https://chrome.google.com/webstore/detail/trotto-go-links/nkeoojidblilnkcbbmfhaeebndapehjk" target="_blank">
           Install the Chrome extension</a> and simply type <span style="color:black">go/[keyword]</span> instead
        of <span style="color:black">trot.to/[keyword]</span>
    `;

    const OPEN_SOURCING_MESSAGE = `
        We've open-sourced the core Trotto app! Contribute code and suggest
        improvements <a href="https://github.com/trotto/go-links" target="_blank">here</a>.
    `;

    const NOTIFICATION_ID_TO_HTML = {
      install_extension: CHROME_INSTALLATION_MESSAGE,
      oss_announcement: OPEN_SOURCING_MESSAGE
    };

    var priorityNotificationId;

    if (browser.name === 'chrome'
        && this.props.userInfo !== undefined
        && (this.props.userInfo && this.props.userInfo.getIn(['notifications', 'install_extension']) !== 'dismissed')
        && !this.props.chromeExtensionInstalled) {
      priorityNotificationId = 'install_extension';
    } else if (new Date().getTime() < 1566648000000
        && this.props.userInfo
        && this.props.userInfo.getIn(['notifications', 'oss_announcement']) !== 'dismissed') {
      priorityNotificationId = 'oss_announcement';
    }

    if (!this.props.errorBarMessage && !priorityNotificationId) {
      return null;
    }
    
    var style = !this.props.errorBarMessage
        ? {paddingLeft: '10px', paddingRight: '10px'}
        : {paddingLeft: '10px', paddingRight: '10px', position: 'fixed', left: '0', top: '0', zIndex: '1000'};

    return (
        <div className="alert alert-warning error-bar" style={style}>
          {this.props.errorBarMessage ?
            <div>
              <span>
                {this.props.errorBarMessage}
              </span>
              &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
              <span
                  style={{textDecoration: 'underline', cursor: 'pointer'}}
                  onClick={this.props.setErrorBarMessage.bind(this, null)}
              >
                Dismiss
              </span>
            </div>
              :
            <div>
              <span
                  dangerouslySetInnerHTML={{__html: NOTIFICATION_ID_TO_HTML[priorityNotificationId]}}
              />
              &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
              <span
                  style={{textDecoration: 'underline', cursor: 'pointer',
                          display: !this.props.userInfo ? 'none' : 'inline'}}
                  onClick={this.props.dismissNotification.bind(this, priorityNotificationId)}
              >
                Dismiss
              </span>
            </div>
          }
        </div>
    );
  }
});


export const ButterbarContainer = connect(
    mapStateToProps,
    actions
)(Butterbar);


export const App = React.createClass({
  render: function () {

    return (
        <div>
          {this.props.children}
        </div>
    )
  }
});
