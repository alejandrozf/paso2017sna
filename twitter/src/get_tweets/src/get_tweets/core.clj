(ns get-tweets.core
  ;;Siple I/O
  (:require [clojure.java.io :as io])
  ;; JSON library
  (:require [cheshire.core :refer :all])
  ;; MongoDB library
  (:require [monger.core :as mg])
  (:import [com.mongodb MongoOptions ServerAddress])
  ;; Twitter API
  (:use [twitter.oauth]
        [twitter.callbacks]
        [twitter.callbacks.handlers]
        [twitter.api.restful])
  (:import [twitter.callbacks.protocols SyncSingleCallback])
  (:gen-class))

(def api-credentials (parse-stream (io/reader "credentials.json")))
(def test-credentials (first api-credentials))

(def my-creds (make-oauth-creds (get test-credentials "consumer_key")
                                (get test-credentials "consumer_secret")
                                (get test-credentials "access_token")
                                (get test-credentials "access_token_secret")))

(def user-id "845696348")
(def user-timeline (statuses-user-timeline :oauth-creds my-creds
                                           :params {:user-id user-id
                                                    :count 5}))
(defn -main
  "I don't do a whole lot ... yet."
  [& args]
  (println "Hello, World!"))
